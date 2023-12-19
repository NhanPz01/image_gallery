const items = document.querySelectorAll('.item');

items.forEach(item => {
    item.addEventListener('mouseenter', () => {
        const actionGroupBtn = item.querySelector('.action-group-btn');
        actionGroupBtn.style.display = 'flex';
    });

    item.addEventListener('mouseleave', () => {
        const actionGroupBtn = item.querySelector('.action-group-btn');
        actionGroupBtn.style.display = 'none';
    });
});

// Biến chứa toàn bộ danh sách các đối tượng (ví dụ: từ Flask)
let images = [];

// Hàm lấy dữ liệu từ nguồn cung cấp (ví dụ: Flask)
function fetchData() {
    fetch('/get_images_list') // Đổi '/get_images_list' thành endpoint của bạn
        .then(response => response.json())
        .then(data => {
            images = data; // Lưu danh sách các đối tượng nhận được từ server

            // Gọi hàm để hiển thị trang đầu tiên
            displayimages(1); // Hiển thị trang đầu tiên khi dữ liệu được tải lên
        })
        .catch(error => console.error('Error:', error));
}

// Hàm hiển thị các đối tượng tương ứng với trang
function displayimages(page) {
    const itemsPerPage = 15;
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const imagesOnPage = images.slice(startIndex, endIndex);

    // Hiển thị các đối tượng trong imagesOnPage (ví dụ: hiển thị ra console)
    console.log(imagesOnPage);

    // Thực hiện việc hiển thị các đối tượng ra giao diện web (ví dụ: hiển thị trong HTML)
    // Đoạn code này cần tùy chỉnh để phù hợp với cách bạn hiển thị dữ liệu trong giao diện của mình
    const imagesContainer = document.getElementById('image-list');
    imagesContainer.innerHTML = ''; // Xóa nội dung cũ trước khi hiển thị trang mới

    imagesOnPage.forEach(object => {
        const objectElement = document.createElement('div');
        objectElement.textContent = object.name; // Thay .name bằng thuộc tính cụ thể của đối tượng

        imagesContainer.appendChild(objectElement);
    });

    // Tạo các nút phân trang (ví dụ: next, prev) và thực hiện các tác vụ điều khiển phân trang
    // Đoạn code này cần tùy chỉnh để tạo ra các nút phân trang và xử lý sự kiện chuyển trang
    // ...
}

// Gọi hàm fetchData() khi trang được tải để lấy dữ liệu
fetchData();
