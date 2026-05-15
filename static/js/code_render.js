function renderTextWithCodeFences(raw) {
    const container = document.createElement("div");
    const pattern = /```(?:([a-zA-Z0-9_+-]+)[ \t]*\r?\n)?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(raw)) !== null) {
        const plain = raw.slice(lastIndex, match.index);
        if (plain) {
            const textBlock = document.createElement("div");
            textBlock.className = "rendered-text";
            textBlock.textContent = plain;
            container.appendChild(textBlock);
        }

        const lang = (match[1] || "").trim();
        const code = (match[2] || "").replace(/^\r?\n/, "");

        const block = document.createElement("div");
        block.className = "code-block";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-sm btn-outline-light code-copy-btn";
        button.textContent = "Copy";

        const pre = document.createElement("pre");
        const codeNode = document.createElement("code");
        if (lang) {
            codeNode.className = `language-${lang}`;
        }
        codeNode.textContent = code;
        pre.appendChild(codeNode);

        button.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(code);
                button.textContent = "Copied";
                setTimeout(() => {
                    button.textContent = "Copy";
                }, 1200);
            } catch (err) {
                button.textContent = "Failed";
                setTimeout(() => {
                    button.textContent = "Copy";
                }, 1200);
            }
        });

        block.appendChild(button);
        block.appendChild(pre);
        container.appendChild(block);

        if (window.hljs) {
            window.hljs.highlightElement(codeNode);
        }

        lastIndex = pattern.lastIndex;
    }

    const tail = raw.slice(lastIndex);
    if (tail) {
        const textBlock = document.createElement("div");
        textBlock.className = "rendered-text";
        textBlock.textContent = tail;
        container.appendChild(textBlock);
    }

    return container;
}

document.addEventListener("DOMContentLoaded", () => {
    const blocks = document.querySelectorAll("[data-code-render]");
    blocks.forEach((el) => {
        const raw = (el.textContent || "").replace(/\r\n/g, "\n");
        const rendered = renderTextWithCodeFences(raw);
        el.innerHTML = "";
        el.appendChild(rendered);
    });
});
