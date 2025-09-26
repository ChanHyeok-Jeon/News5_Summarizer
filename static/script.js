document.addEventListener("DOMContentLoaded", () => {
    initializeSearchForm();
    initializeNewsLinks();
    initializeAnimations();
});

// 검색 폼 초기화
function initializeSearchForm() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = searchForm?.querySelector('input');
    const searchButton = searchForm?.querySelector('button');
    
    if (!searchForm) return;

    // 검색 폼 제출 처리
    searchForm.addEventListener('submit', (e) => {
        if (!searchInput.value.trim()) {
            e.preventDefault();
            showNotification('검색어를 입력해주세요', 'warning');
            return;
        }

        // 로딩 상태 표시
        const btnText = searchButton.querySelector('.btn-text');
        const loadingText = searchButton.querySelector('.loading');
        
        if (btnText && loadingText) {
            btnText.style.display = 'none';
            loadingText.style.display = 'inline';
        }
        
        searchButton.disabled = true;
        searchButton.style.cursor = 'not-allowed';
    });

    // 검색 입력 필드 포커스 효과
    searchInput.addEventListener('focus', () => {
        searchForm.style.transform = 'scale(1.02)';
        searchForm.style.transition = 'transform 0.3s ease';
    });
    
    searchInput.addEventListener('blur', () => {
        searchForm.style.transform = 'scale(1)';
    });

    // 실시간 검색어 유효성 체크
    searchInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (value.length > 50) {
            showNotification('검색어는 50자 이내로 입력해주세요', 'warning');
            e.target.value = value.substring(0, 50);
        }
    });
}

// 뉴스 링크 초기화
function initializeNewsLinks() {
    const newsLinks = document.querySelectorAll(".news-link");

    newsLinks.forEach((link, index) => {
        // 클릭 이벤트 로깅
        link.addEventListener("click", (e) => {
            const title = link.querySelector('h3')?.textContent || '제목 없음';
            console.log(`뉴스 요약 요청 [${index + 1}]:`, title);
            
            // 클릭 피드백 애니메이션
            const newsItem = link.closest('.news-item');
            newsItem.style.transform = 'scale(0.98)';
            
            setTimeout(() => {
                newsItem.style.transform = '';
            }, 150);

            // 요약 로딩 상태를 localStorage에 저장 (페이지 이동 후 사용)
            try {
                sessionStorage.setItem('newsClickTime', Date.now().toString());
                sessionStorage.setItem('newsTitle', title);
            } catch (e) {
                // sessionStorage 사용 불가시 무시
            }
        });

        // 키보드 접근성
        link.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                link.click();
            }
        });
    });
}

// 애니메이션 초기화
function initializeAnimations() {
    // Intersection Observer로 뷰포트 진입 시 애니메이션
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // 뉴스 아이템 관찰
    document.querySelectorAll('.news-item').forEach(item => {
        observer.observe(item);
    });

    // 페이지네이션 버튼 호버 효과
    document.querySelectorAll('.pagination-btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    // 기존 알림 제거
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    // 알림 요소 생성
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 스타일 적용
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '600',
        fontSize: '14px',
        zIndex: '1000',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        maxWidth: '300px',
        wordWrap: 'break-word'
    });

    // 타입별 배경색
    const colors = {
        info: '#3498db',
        success: '#2ecc71',
        warning: '#f39c12',
        error: '#e74c3c'
    };
    notification.style.backgroundColor = colors[type] || colors.info;

    // DOM에 추가
    document.body.appendChild(notification);

    // 애니메이션으로 표시
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    // 3초 후 자동 제거
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

// 이미지 로딩 에러 처리
document.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG') {
        const img = e.target;
        img.style.display = 'none';
        
        // 이미지 컨테이너에 대체 텍스트 표시
        const container = img.closest('.news-image');
        if (container) {
            container.innerHTML = '<div class="image-placeholder">📰</div>';
            container.style.cssText += `
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                color: #6c757d;
                font-size: 2rem;
            `;
        }
    }
}, true);

// 부드러운 스크롤 함수
function smoothScrollTo(element, duration = 800) {
    const targetPosition = element.offsetTop - 100;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = easeInOutQuad(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    function easeInOutQuad(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    requestAnimationFrame(animation);
}

// 요약 페이지용 함수들
if (window.location.pathname === '/summary') {
    // 요약 완료 후 실행
    window.addEventListener('load', () => {
        // sessionStorage에서 클릭 정보 확인
        try {
            const clickTime = sessionStorage.getItem('newsClickTime');
            const newsTitle = sessionStorage.getItem('newsTitle');
            
            if (clickTime && newsTitle) {
                const elapsed = Date.now() - parseInt(clickTime);
                console.log(`요약 페이지 로드 완료 (${elapsed}ms 소요): ${newsTitle}`);
                
                // 사용 후 제거
                sessionStorage.removeItem('newsClickTime');
                sessionStorage.removeItem('newsTitle');
            }
        } catch (e) {
            // sessionStorage 사용 불가시 무시
        }
    });
}

// 페이지 성능 모니터링
window.addEventListener('load', () => {
    // 페이지 로드 성능 측정
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`페이지 로드 시간: ${loadTime}ms`);
        
        // 느린 로딩 시 사용자에게 알림
        if (loadTime > 3000) {
            setTimeout(() => {
                showNotification('네트워크가 느려 로딩에 시간이 걸렸습니다', 'warning');
            }, 1000);
        }
    }
});

// 키보드 단축키
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: 검색 입력 포커스
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-form input');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // ESC: 검색 입력 블러
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('.search-form input');
        if (searchInput && document.activeElement === searchInput) {
            searchInput.blur();
        }
    }
});

// 다크 모드 감지 및 대응 (시스템 설정 기반)
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.body.classList.add('dark-mode');
}

// 다크 모드 변경 감지
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (e.matches) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
});

// 오프라인 상태 감지
window.addEventListener('online', () => {
    showNotification('인터넷 연결이 복구되었습니다', 'success');
});

window.addEventListener('offline', () => {
    showNotification('인터넷 연결이 끊어졌습니다', 'error');
});

// 뉴스 카드 lazy loading 최적화
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            }
        });
    });

    // 이미지 요소들을 관찰 대상에 추가
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// 유틸리티 함수: 디바운스
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 검색어 자동완성 (향후 구현용 기반 코드)
function initializeAutoComplete() {
    const searchInput = document.querySelector('.search-form input');
    if (!searchInput) return;

    const debouncedSearch = debounce((query) => {
        if (query.length > 2) {
            // TODO: 서버에서 자동완성 검색어 가져오기
            console.log('자동완성 검색:', query);
        }
    }, 300);

    searchInput.addEventListener('input', (e) => {
        debouncedSearch(e.target.value.trim());
    });
}