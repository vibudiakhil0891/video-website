// ================= ELEMENTS =================
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const fileNameDisplay = document.getElementById("fileName");
const dropArea = document.getElementById("dropArea");
const categorySelect = document.getElementById("categorySelect");

const contactForm = document.querySelector("form[action='/contact']");
const searchInput = document.getElementById("searchInput");
const filterSelect = document.getElementById("filterSelect");
const galleryCards = document.getElementById("galleryCards");

const sections = document.querySelectorAll("section");
const navLinks = document.querySelectorAll(".navbar a");

// ================= FILE HANDLING =================

// Handle file selection
function handleFile(file) {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("video/")) {
        alert("Please select a valid video file!");
        return;
    }

    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
        alert("File too large! Max 100MB allowed.");
        return;
    }

    // Display file name
    if (fileNameDisplay) {
        fileNameDisplay.textContent = file.name;
    }

    // Show preview
    if (preview) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
}

// File input change event
if (fileInput) {
    fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));
}

// Drag & Drop functionality
if (dropArea && fileInput) {
    ['dragenter', 'dragover'].forEach(event => {
        dropArea.addEventListener(event, (e) => {
            e.preventDefault();
            dropArea.style.background = "#334155";
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropArea.addEventListener(event, (e) => {
            e.preventDefault();
            dropArea.style.background = "#1e293b";
        });
    });

    dropArea.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files[0];
        fileInput.files = e.dataTransfer.files;
        handleFile(file);
    });

    dropArea.addEventListener("click", () => fileInput.click());
}

// ================= CONTACT FORM =================
if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(contactForm);
        const submitBtn = contactForm.querySelector("button");

        submitBtn.textContent = "Sending...";
        submitBtn.disabled = true;

        try {
            const res = await fetch(contactForm.action, {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                alert("Message sent successfully!");
                contactForm.reset();
            } else {
                alert("Failed to send message.");
            }
        } catch (err) {
            alert("Error: " + err.message);
        } finally {
            submitBtn.textContent = "Send Message";
            submitBtn.disabled = false;
        }
    });
}

// ================= GALLERY FILTER =================
function filterGallery() {
    if (!galleryCards) return;

    const search = searchInput.value.toLowerCase();
    const category = filterSelect.value;

    Array.from(galleryCards.children).forEach(card => {
        const title = card.querySelector("p").textContent.toLowerCase();
        const cardCategory = card.getAttribute("data-category");

        const matchSearch = title.includes(search);
        const matchCategory = category === "all" || category === cardCategory;

        card.style.display = (matchSearch && matchCategory) ? "block" : "none";
    });
}

if (searchInput) searchInput.addEventListener("input", filterGallery);
if (filterSelect) filterSelect.addEventListener("change", filterGallery);

// ================= SMOOTH SCROLL =================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth" });
        }
    });
});

// ================= NAVBAR ACTIVE LINK =================
window.addEventListener("scroll", () => {
    let current = "";

    sections.forEach(section => {
        const top = section.offsetTop - 80;
        if (window.scrollY >= top) {
            current = section.getAttribute("id");
        }
    });

    navLinks.forEach(link => {
        link.classList.remove("active");
        if (link.getAttribute("href") === "#" + current) {
            link.classList.add("active");
        }
    });
});
