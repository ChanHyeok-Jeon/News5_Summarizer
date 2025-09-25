// 기본적으로 큰 기능은 백엔드에서 처리하므로
// 여기서는 주로 UX 개선, 클릭 이벤트 로그 등 작성 가능

document.addEventListener("DOMContentLoaded", () => {
    const links = document.querySelectorAll(".news-link");

    links.forEach(link => {
        link.addEventListener("click", () => {
            console.log("뉴스 요약 요청:", link.textContent);
        });
    });
});
