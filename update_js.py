import re

file_path = '/Users/henryuhl/Documents/GitHub/susanneuhl.github.io/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update openFullscreen and related modal functions
# We need to track all clickable project items to allow navigation
new_modal_js = """
        let currentProjectIndex = -1;
        let allProjectItems = [];

        function updateProjectItems() {
            // Collect all li items that are currently visible (for filtering support)
            allProjectItems = Array.from(document.querySelectorAll('.main-container li')).filter(li => li.style.display !== 'none');
        }

        function openFullscreen(src, element) {
            const modal = document.getElementById("fullscreenModal");
            const image = document.getElementById("fullscreenImage");
            const modalCredit = document.getElementById("modalCredit");
            
            updateProjectItems();
            currentProjectIndex = allProjectItems.indexOf(element);
            
            // Body-Scroll sperren
            document.body.style.overflow = 'hidden';
            
            updateModalContent(element);
            modal.classList.add("show");
        }

        function updateModalContent(element) {
            const image = document.getElementById("fullscreenImage");
            const modalCredit = document.getElementById("modalCredit");
            
            if (!element) return;

            // 1) Get high-res source
            let imageSrc = element.querySelector('img').src;
            const fullAvif = element.getAttribute('data-full-avif');
            if (fullAvif) {
                imageSrc = fullAvif;
            } else {
                const picture = element.querySelector('picture');
                if (picture) {
                    const avifSource = picture.querySelector('source[type="image/avif"]');
                    if (avifSource && avifSource.srcset) {
                        if (avifSource.srcset.startsWith('images/thumbs/')) {
                            const base = avifSource.srcset.replace('images/thumbs/', '').replace(/\\.avif$/, '');
                            imageSrc = `images/compressed/${base}.avif`;
                        } else {
                            imageSrc = avifSource.srcset;
                        }
                    }
                }
            }
            
            image.src = imageSrc;
            
            // 2) Update Credit
            const creditSpan = element.querySelector('.image-credit');
            if (creditSpan) {
                modalCredit.textContent = creditSpan.textContent;
                modalCredit.style.display = 'block';
            } else {
                modalCredit.style.display = 'none';
            }
        }

        function nextImage(event) {
            if (event) event.stopPropagation();
            if (allProjectItems.length === 0) updateProjectItems();
            currentProjectIndex = (currentProjectIndex + 1) % allProjectItems.length;
            updateModalContent(allProjectItems[currentProjectIndex]);
        }

        function prevImage(event) {
            if (event) event.stopPropagation();
            if (allProjectItems.length === 0) updateProjectItems();
            currentProjectIndex = (currentProjectIndex - 1 + allProjectItems.length) % allProjectItems.length;
            updateModalContent(allProjectItems[currentProjectIndex]);
        }

        function closeFullscreen() {
            const modal = document.getElementById("fullscreenModal");
            modal.classList.remove("show");
            // Body-Scroll wieder freigeben
            document.body.style.overflow = '';
        }

        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                closeFullscreen();
            } else if (event.key === "ArrowRight") {
                const modal = document.getElementById("fullscreenModal");
                if (modal.classList.contains('show')) nextImage();
            } else if (event.key === "ArrowLeft") {
                const modal = document.getElementById("fullscreenModal");
                if (modal.classList.contains('show')) prevImage();
            }
        });
"""

# Replace the existing openFullscreen and closeFullscreen functions
# Regex to find from 'function openFullscreen' to the end of closeFullscreen
content = re.sub(r'function\s+openFullscreen\(src,\s*element\)\s*\{[\s\S]*?function\s+closeFullscreen\(\)\s*\{[\s\S]*?\}', new_modal_js, content)

# 2. Add Scroll Reveal (Intersection Observer)
scroll_reveal_js = """
        // Scroll Reveal Animation
        document.addEventListener('DOMContentLoaded', function() {
            const revealCallback = (entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            };

            const revealObserver = new IntersectionObserver(revealCallback, {
                root: null,
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            const initReveal = () => {
                const revealElements = document.querySelectorAll('.reveal');
                revealElements.forEach(el => revealObserver.observe(li)); // Error here, should be el
            };
"""
# Wait, let me fix the snippet above before writing
scroll_reveal_js = """
        // Scroll Reveal Animation
        document.addEventListener('DOMContentLoaded', function() {
            const revealCallback = (entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
            };

            const revealObserver = new IntersectionObserver(revealCallback, {
                root: null,
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            const initReveal = () => {
                const revealElements = document.querySelectorAll('.reveal');
                revealElements.forEach(el => revealObserver.observe(el));
            };
            
            // Initial call
            initReveal();
            
            // Re-initialize if the grid changes (for mobile timeline)
            const mainContainer = document.querySelector('.main-container');
            const gridObserver = new MutationObserver(() => {
                initReveal();
            });
            gridObserver.observe(mainContainer, { childList: true });
        });
"""

# Append scroll reveal JS after the modal functions
content = content.replace(new_modal_js, new_modal_js + scroll_reveal_js)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)






