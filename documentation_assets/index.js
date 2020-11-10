let select = (el) => document.querySelector(el),
    selectAll = (els) => document.querySelectorAll(els),
    toc = select(".table-of-contents");

toc = toc.querySelectorAll("ul")[0];

enableExpansion(toc.children);

function enableExpansion(children, layer = 1) {
    // console.log(children);
    [...children].map((n) => {
        let uls = n.querySelectorAll(`.lay${layer+1}`),
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
                enableExpansion(el.children, layer+1);
            });
        };
    });
}
