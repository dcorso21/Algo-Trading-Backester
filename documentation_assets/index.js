let select = (el) => document.querySelector(el),
    selectAll = (els) => document.querySelectorAll(els),
    toc = select(".table-of-contents");

const main = select(".main");

toc = toc.querySelectorAll("ul")[0];
enableExpansion(toc.children);
enableDarkMode();

function enableExpansion(children, layer = 1) {
    // console.log(children);
    [...children].map((n) => {
        let uls = n.querySelectorAll(`.lay${layer + 1}`),
            expand = n.querySelector(".expand");

        if (!expand) return;

        expand.onclick = () => {
            if (layer === 1) {
                let lay2 = selectAll(".lay2"),
                    lay3 = selectAll(".lay3");
                [...lay2, ...lay3].map((el) => {
                    if (
                        !el.classList.contains("toggleview") &&
                        ![...uls].includes(el)
                    ) {
                        el.classList.add("toggleView");
                    }
                });
            }

            console.log(uls);

            [...uls].map((el) => {
                el.classList.toggle("toggleView");
                enableExpansion(el.children, layer + 1);
            });
        };
    });
}

function enableDarkMode() {
    let darkMode = select(".darkMode");
    let body = select("body");
    darkMode.onclick = () => {
        body.classList.toggle("dark");
        if (body.classList.contains("dark")) {
            darkMode.classList.remove("fa-moon");
            darkMode.classList.add("fa-sun");
        } else {
            darkMode.classList.remove("fa-sun");
            darkMode.classList.add("fa-moon");
        }
    };
}

let menu = select("#menu");
let menuContents = select("#menu-contents");
menuContents.classList.add("fadeOut");
let menuToggle = select("#menu-toggle");
let isOpen = false;
menuToggle.onclick = () => {
    if (isOpen) {
        isOpen = !isOpen;
        menu.classList.remove("open");
        menu.classList.add("close");
        menuToggle.classList.remove("fa-chevron-left")
        menuToggle.classList.add("fa-bars")
    } else {
        isOpen = !isOpen;
        menu.classList.remove("close");
        menu.classList.add("open");
        menuToggle.classList.remove("fa-bars")
        menuToggle.classList.add("fa-chevron-left")
    }
};

let scrolling = false;
let navTitleVisible = false;
let navTitle = select("#nav-title");

main.onscroll = (e) => {
    if (scrolling) return;
    scrolling = true;

    if (navTitleVisible) {
        if (e.target.scrollTop <= 300) {
            navTitle.innerHTML = "";
            navTitleVisible = false;
        }
    } else {
        if (e.target.scrollTop > 300) {
            navTitle.innerHTML = "Algorithmic Trading Backtester";
            navTitleVisible = true;
        }
    }
    setTimeout(() => {
        scrolling = false;
    }, 100);
};
