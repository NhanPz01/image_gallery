// modal.js
document.addEventListener('DOMContentLoaded', (event) => {
    const modal = document.getElementById("myModal");
    const modalImg = document.getElementById("modalImage");
    const modalUsername = document.getElementById("modalUsername");
    const modalUploadTime = document.getElementById("modalUploadTime");
    const modalTags = document.getElementById("modalTags");
    const modalDownloadLink = document.getElementById("modalDownloadLink");
    const closeBtn = document.querySelector(".close");
    const modalContent = document.querySelector(".modal-content");
  
    const images = document.querySelectorAll(".gallery-image");
  
    images.forEach(img => {
      img.addEventListener('click', () => {
        modal.style.display = "block";
        modalImg.src = img.src;
        modalUsername.textContent = "Username: " + img.dataset.username;
        modalUploadTime.textContent = "Upload Time: " + img.dataset.uploadTime;
        modalTags.textContent = "Tags: " + img.dataset.tags;
        modalDownloadLink.href = img.src;
      });
    });
  
    const closeModal = () => {
      modal.style.display = "none";
      modalImg.src = "";
      modalUsername.textContent = "";
      modalUploadTime.textContent = "";
      modalDownloadLink.href = "";
    };
  
    closeBtn.addEventListener('click', closeModal);
    modalContent.addEventListener('click', closeModal);
  });