let select = (el) => document.querySelector(el),
    selectAll = (els) => document.querySelectorAll(els),
    toc = select(".table-of-contents");

toc = toc.querySelectorAll("ul")[0];

enableExpansion(toc.children);

function enableExpansion(children) {
    console.log(children);
    [...children].map((n) => {
        let uls = n.querySelectorAll("ul"),
            expand = n.querySelector(".expand");

        if (!expand) return;

        expand.onclick = () => {
            [...uls].map((el) => {
                el.classList.toggle("toggleView");
                enableExpansion(el.children);
            });
        };
    });
}
