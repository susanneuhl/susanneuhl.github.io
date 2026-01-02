/**
 * WebGL Depth Map Parallax Effect
 * Creates a 3D depth effect using a displacement map.
 */

class DepthEffect {
    constructor(container, imageSrc, mapSrc) {
        this.container = container;
        this.imageSrc = imageSrc;
        this.mapSrc = mapSrc;
        this.raf = null;
        
        this.canvas = document.createElement('canvas');
        this.canvas.classList.add('depth-canvas');
        this.container.appendChild(this.canvas);
        this.gl = this.canvas.getContext('webgl');

        if (!this.gl) {
            console.warn('WebGL not supported');
            return;
        }

        this.mouse = { x: 0, y: 0 };
        this.targetMouse = { x: 0, y: 0 };
        this.rect = this.container.getBoundingClientRect();
        
        // Shader Sources
        this.vertexShaderSrc = `
            attribute vec2 position;
            attribute vec2 texCoord;
            varying vec2 vTexCoord;
            void main() {
                gl_Position = vec4(position, 0.0, 1.0);
                vTexCoord = texCoord;
            }
        `;

        this.fragmentShaderSrc = `
            precision mediump float;
            uniform sampler2D uImage;
            uniform sampler2D uMap;
            uniform vec2 uMouse;
            uniform vec2 uImageScale;
            uniform vec2 uImageOffset;
            varying vec2 vTexCoord;

            void main() {
                // Adjust coords for object-fit: cover
                vec2 coverCoord = vTexCoord * uImageScale + uImageOffset;
                
                // If out of bounds, discard or clamp (though our math ensures we are 'zooming in' on texture, 
                // so the range is 0..1 or smaller subset of texture, so we are always inside texture [0,1]?)
                // Wait. 
                // If CanvasRatio > ImageRatio (Wider): scaleY < 1. Range is e.g. 0.25 to 0.75. Safe.
                // If CanvasRatio < ImageRatio (Taller): scaleX < 1. Range is e.g. 0.25 to 0.75. Safe.
                // We are mapping 0..1 (Canvas) to a subset of Texture.
                
            vec4 depthDistortion = texture2D(uMap, coverCoord);
            float parallaxScale = 0.04; // Increased intensity (was 0.015)
                
                vec2 parallax = uMouse * depthDistortion.r * parallaxScale;
                vec2 finalCoord = coverCoord + parallax;

                gl_FragColor = texture2D(uImage, finalCoord);
            }
        `;

        this.init();
    }

    async init() {
        // Load Images
        try {
            const [img, map] = await Promise.all([
                this.loadImage(this.imageSrc),
                this.loadImage(this.mapSrc)
            ]);
            
            this.img = img;
            this.map = map;
            
            // Setup WebGL
            this.program = this.createProgram(this.vertexShaderSrc, this.fragmentShaderSrc);
            this.gl.useProgram(this.program);
            
            this.setupBuffers();
            this.setupTextures();
            this.resize();
            this.setupEvents();
            
            // Watch for container size changes (handles lazy-loaded images better than window resize)
            this.resizeObserver = new ResizeObserver(() => {
                this.resize();
            });
            this.resizeObserver.observe(this.container);
            
            this.render();

            // Mark container as ready so we can hide the base image
            this.container.classList.add('depth-ready');
            
        } catch (e) {
            console.error('Failed to load depth effect assets:', e);
            // On error, ensure base image stays visible
            if (this.canvas && this.canvas.parentNode) {
                this.canvas.parentNode.removeChild(this.canvas);
            }
        }
    }

    loadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    }

    createShader(type, source) {
        const shader = this.gl.createShader(type);
        this.gl.shaderSource(shader, source);
        this.gl.compileShader(shader);
        if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
            console.error(this.gl.getShaderInfoLog(shader));
            this.gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    createProgram(vsSrc, fsSrc) {
        const vs = this.createShader(this.gl.VERTEX_SHADER, vsSrc);
        const fs = this.createShader(this.gl.FRAGMENT_SHADER, fsSrc);
        const program = this.gl.createProgram();
        this.gl.attachShader(program, vs);
        this.gl.attachShader(program, fs);
        this.gl.linkProgram(program);
        if (!this.gl.getProgramParameter(program, this.gl.LINK_STATUS)) {
            console.error(this.gl.getProgramInfoLog(program));
            return null;
        }
        return program;
    }

    setupBuffers() {
        const positions = new Float32Array([
            -1, -1,
             1, -1,
            -1,  1,
             -1,  1,
             1, -1,
             1,  1,
        ]);
        
        const texCoords = new Float32Array([
            0, 1,
            1, 1,
            0, 0,
            0, 0,
            1, 1,
            1, 0,
        ]);

        const positionBuffer = this.gl.createBuffer();
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, positionBuffer);
        this.gl.bufferData(this.gl.ARRAY_BUFFER, positions, this.gl.STATIC_DRAW);
        
        const positionLoc = this.gl.getAttribLocation(this.program, 'position');
        this.gl.enableVertexAttribArray(positionLoc);
        this.gl.vertexAttribPointer(positionLoc, 2, this.gl.FLOAT, false, 0, 0);

        const texCoordBuffer = this.gl.createBuffer();
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, texCoordBuffer);
        this.gl.bufferData(this.gl.ARRAY_BUFFER, texCoords, this.gl.STATIC_DRAW);
        
        const texCoordLoc = this.gl.getAttribLocation(this.program, 'texCoord');
        this.gl.enableVertexAttribArray(texCoordLoc);
        this.gl.vertexAttribPointer(texCoordLoc, 2, this.gl.FLOAT, false, 0, 0);
    }

    setupTextures() {
        // Texture 0: Image
        const texture0 = this.gl.createTexture();
        this.gl.activeTexture(this.gl.TEXTURE0);
        this.gl.bindTexture(this.gl.TEXTURE_2D, texture0);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);
        this.gl.texImage2D(this.gl.TEXTURE_2D, 0, this.gl.RGBA, this.gl.RGBA, this.gl.UNSIGNED_BYTE, this.img);
        this.gl.uniform1i(this.gl.getUniformLocation(this.program, 'uImage'), 0);

        // Texture 1: Map
        const texture1 = this.gl.createTexture();
        this.gl.activeTexture(this.gl.TEXTURE1);
        this.gl.bindTexture(this.gl.TEXTURE_2D, texture1);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);
        this.gl.texImage2D(this.gl.TEXTURE_2D, 0, this.gl.RGBA, this.gl.RGBA, this.gl.UNSIGNED_BYTE, this.map);
        this.gl.uniform1i(this.gl.getUniformLocation(this.program, 'uMap'), 1);
    }

    resize() {
        this.rect = this.container.getBoundingClientRect();
        this.canvas.width = this.rect.width;
        this.canvas.height = this.rect.height;
        this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        
        this.updateCoverUVs();
    }
    
    updateCoverUVs() {
        if (!this.img) return;
        
        const cw = this.canvas.width;
        const ch = this.canvas.height;
        const iw = this.img.width;
        const ih = this.img.height;
        
        const canvasRatio = cw / ch;
        const imageRatio = iw / ih;
        
        let scaleX = 1.0;
        let scaleY = 1.0;
        let offsetX = 0.0;
        let offsetY = 0.0;
        
        // Emulate object-fit: cover
        if (canvasRatio > imageRatio) {
            // Canvas is wider relative to height -> Crop top/bottom
            // We map 0..1 (Canvas Y) to a smaller range of Texture Y
            scaleY = imageRatio / canvasRatio;
            offsetY = (1.0 - scaleY) / 2.0;
        } else {
            // Canvas is taller relative to width -> Crop left/right
            // We map 0..1 (Canvas X) to a smaller range of Texture X
            scaleX = canvasRatio / imageRatio;
            offsetX = (1.0 - scaleX) / 2.0;
        }
        
        const uScaleLoc = this.gl.getUniformLocation(this.program, 'uImageScale');
        const uOffsetLoc = this.gl.getUniformLocation(this.program, 'uImageOffset');
        
        if (uScaleLoc) this.gl.uniform2f(uScaleLoc, scaleX, scaleY);
        if (uOffsetLoc) this.gl.uniform2f(uOffsetLoc, offsetX, offsetY);
    }

    setupEvents() {
        this.container.addEventListener('mousemove', (e) => {
            // IMPORTANT: Get fresh rect on every mousemove to account for scrolling
            const rect = this.container.getBoundingClientRect();
            
            // Normalize -1 to 1
            const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            const y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
            
            // Mouse direction mapping
            // Inverted Y so up is up.
            // X is kept standard so moving mouse right moves view right (revealing left side of depth)
            this.targetMouse = { x: -x, y: -y };
        });

        this.container.addEventListener('mouseleave', () => {
            this.targetMouse = { x: 0, y: 0 };
        });
    }

    render() {
        // Smooth interpolation
        this.mouse.x += (this.targetMouse.x - this.mouse.x) * 0.05;
        this.mouse.y += (this.targetMouse.y - this.mouse.y) * 0.05;

        this.gl.uniform2f(this.gl.getUniformLocation(this.program, 'uMouse'), this.mouse.x, this.mouse.y);

        this.gl.drawArrays(this.gl.TRIANGLES, 0, 6);
        this.raf = requestAnimationFrame(() => this.render());
    }

    dispose() {
        try {
            if (this.raf) cancelAnimationFrame(this.raf);
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
                this.resizeObserver = null;
            }
            if (this.canvas && this.canvas.parentNode) {
                this.canvas.parentNode.removeChild(this.canvas);
            }
            this.container.classList.remove('depth-ready');
            this.gl = null;
        } catch (err) {
            console.warn('DepthEffect dispose error', err);
        }
    }
}

// ---- Simple Auto-init (no lazy loading) ----
(function() {
    document.addEventListener('DOMContentLoaded', () => {
        const isLargeScreen = window.innerWidth > 900;
        const isMouse = window.matchMedia('(hover: hover)').matches;
        
        if (!isLargeScreen && !isMouse) {
            console.log('Depth Effect: mobile detected, skip init');
            return;
        }

        const containers = document.querySelectorAll('[data-depth-map]');
        console.log(`Depth Effect: Initializing ${containers.length} effects`);

        containers.forEach(container => {
            const img = container.querySelector('img');
            const mapSrc = container.getAttribute('data-depth-map');
            
            if (!img || !mapSrc) return;

            const initEffect = () => {
                // Double-check image has dimensions before initializing
                if (!img.naturalWidth || !img.naturalHeight) {
                    console.warn(`✗ Image has no dimensions yet: ${mapSrc}`);
                    return;
                }
                
                try {
                    new DepthEffect(container, img.currentSrc || img.src, mapSrc);
                    console.log(`✓ Depth effect ready: ${mapSrc}`);
                } catch (err) {
                    console.warn(`✗ Depth effect failed: ${mapSrc}`, err);
                }
            };

            if (img.complete && img.naturalWidth > 0) {
                // Image already loaded, but wait a bit for layout to settle
                setTimeout(initEffect, 100);
            } else {
                // Wait for image to fully load
                img.addEventListener('load', () => {
                    setTimeout(initEffect, 100);
                }, { once: true });
            }
        });
    });
})();

