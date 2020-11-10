let select = (el) => document.querySelector(el),
    selectAll = (els) => document.querySelectorAll(els),
    toc = select('.table-of-contents');


toc = toc.querySelectorAll('ul')[0];


console.log(toc.childNodes);


[...toc.childNodes].map((n) => {
    n.onclick = () => {
        console.log(n);
        if (!n.childNodes) return;
        [...n.childNodes].map((c) => {
            n.style.display = 'block'
        })
    }
})



