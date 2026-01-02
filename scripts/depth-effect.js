/**
 * WebGL Depth Map Parallax Effect
 * Creates a 3D depth effect using a displacement map.
 */

class DepthEffect {
    constructor(container, imageSrc, mapSrc) {
        this.container = container;
        this.imageSrc = imageSrc;
        this.mapSrc = mapSrc;
        
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
            varying vec2 vTexCoord;

            void main() {
                vec4 depthDistortion = texture2D(uMap, vTexCoord);
                float parallaxScale = 0.015; // Intensity of effect
                
                // Mouse direction affects offset direction
                // Depth (0-1) determines how much it moves
                // Bright = Near = Moves more/opposite to background
                
                vec2 parallax = uMouse * depthDistortion.r * parallaxScale;
                
                // Final coord
                vec2 finalCoord = vTexCoord + parallax;

                // Simple edge clamping to prevent wrapping artifacts if needed
                // For now, we rely on texture params CLAMP_TO_EDGE
                
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
            this.render();
            
            window.addEventListener('resize', () => this.resize());
            
        } catch (e) {
            console.error('Failed to load depth effect assets:', e);
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
    }

    setupEvents() {
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.rect;
            // Normalize -1 to 1
            const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            const y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
            
            // Invert logic: 
            // If I move mouse right (x>0), background should move left, foreground (depth) moves right?
            // Usually: Perspective move.
            this.targetMouse = { x: x, y: -y };
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
        requestAnimationFrame(() => this.render());
    }
}

// Auto-Init logic
document.addEventListener('DOMContentLoaded', () => {
    // Only on desktop
    if (window.matchMedia('(hover: none)').matches) return;

    const containers = document.querySelectorAll('[data-depth-map]');
    containers.forEach(container => {
        const img = container.querySelector('img');
        const mapSrc = container.getAttribute('data-depth-map');
        
        if (img && mapSrc) {
            // Wait for image to load to get intrinsic size if needed, 
            // but for now we rely on CSS size.
            // Using the 'high-res' source for the effect if available in picture
            
            // Find best image source
            let imageSrc = img.src;
            // If picture element used, we might want the biggest one, but img.src usually holds the current one.
            
            // For Susanne's site specifically: 
            // The thumbnails are small, but we want the effect on the thumbnail.
            // We use the same image source as the <img> tag.
            
            new DepthEffect(container, imageSrc, mapSrc);
        }
    });
});

