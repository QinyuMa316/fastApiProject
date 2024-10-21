async function fetchAndRenderTree() {
    try {
        const response = await fetch("/api/tree");
        const treeData = await response.json();
        renderTree(treeData);
    } catch (error) {
        console.error("Error fetching tree data:", error);
    }
}

async function fetchAndRenderDouble() {
    try{
        const response = await fetch("/api/double");
        console.log("Fetching double tree data");
        const doubleTree = await response.json();
        renderDoubleTree(doubleTree['bigTree'], doubleTree['smallTree']);
    } catch (error) {
        console.error("Error fetching tree data:", error);
    }
}

// document.addEventListener("DOMContentLoaded", fetchAndRenderTree);

document.addEventListener("DOMContentLoaded", fetchAndRenderDouble);

function renderTree(treeData) {


    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.59; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const tree = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1.5) / a.depth);

    // Sort the tree and apply the layout.
    const root = tree(d3.hierarchy(treeData)
        .sort((a, b) => d3.ascending(a.data.name, b.data.name)));

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(root.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y));

    // Append nodes.
    // svg.append("g")
    //   .selectAll()
    //   .data(root.descendants())
    //   .join("circle")
    //     .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
    //     .attr("fill", d => d.children ? "#555" : "#999")
    //     .attr("r", 2.5);

    // Append nodes.
    // svg.append("g")
    //   .selectAll()
    //   .data(root.descendants())
    //   .join("circle")
    //     .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
    //     .attr("fill", d => {
    //       if (!d.children) return "#8ecfc9"; // 叶子节点
    //       else if (d === root) return "#82b0d2"; // 根节点
    //       else return "#beb8dc"; // 中间节点
    //     })
    //     .attr("r", 4); // 节点大小设置2.5

    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(root.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        .attr("fill", d => {
            if (!d.children) return "#8ecfc9";// 叶子节点
            else if (d.data.name === root.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2";// 中间节点
        })
        .attr("r", 4);

    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        .text(d => {
            if (!d.children) {
                // 如果是叶子节点
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
        })  // 为每个节点分配序号，从 1 开始
        .attr("font-size", "10px")  // 设置字体大小
        .attr("fill", "black");  // 设置字体颜色

    // Append labels.
    // svg.append("g")
    //     .attr("stroke-linejoin", "round")
    //     .attr("stroke-width", 3)
    //   .selectAll()
    //   .data(root.descendants())
    //   .join("text")
    //     .filter(d => !d.children) // new added
    //     .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0) rotate(${d.x >= Math.PI ? 180 : 0})`)
    //     .attr("dy", "0.31em")
    //     .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
    //     .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
    //     .attr("paint-order", "stroke")
    //     .attr("stroke", "white")
    //     .attr("fill", "currentColor")
    //     .text(d => d.data.name);

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    sortedEntries.forEach(([substance, idx]) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${idx}</td><td>${substance}</td>`;
        tbody.appendChild(row);
    });

}

function renderDoubleTree(bigTreeData, smallTreeData){
        // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.5; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const treeLayout = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1) / a.depth);

    // Sort the tree and apply the layout.
    const bigTreeRoot = d3.hierarchy(bigTreeData);
    const smallTreeRoot = d3.hierarchy(smallTreeData);
    treeLayout(bigTreeRoot);

    // 初始化大树所有节点的isPathPoint属性为false
    bigTreeRoot.each(d => d.isPathPoint = false);

    // 层次遍历获取小树的节点集合
    const smallTreeLevels = getNodesByLevel(smallTreeRoot);

    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths(bigTreeRoot, smallTreeLevels);

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(bigTreeRoot.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y));

    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(bigTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        .attr("fill", d => {
            if (!d.children) return "#8ecfc9";// 叶子节点
            else if (d.data.name === bigTreeRoot.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2";// 中间节点
        })
        .attr("r", 4)
        .attr("class", d => d.isPathPoint ? "highlight" : "normal");

    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        .text(d => {
            if (!d.children) {
                // 如果是叶子节点
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
        })  // 为每个节点分配序号，从 1 开始
        .attr("font-size", "10px")  // 设置字体大小
        .attr("fill", "black");  // 设置字体颜色

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    const datasPerRow = 3;
    let currentRow = document.createElement("tr");
    sortedEntries.forEach(([substance, idx]) => {
        const cell = document.createElement('td');
        cell.innerHTML = `<td>${idx}: ${substance}</td>`;
        currentRow.appendChild(cell);

        if(idx % datasPerRow === 0) {
            tbody.appendChild(currentRow);
            currentRow = document.createElement("tr");
        }
    });

    // 下载按钮
    // 下载SVG图像
    // Add download button
    const button = document.getElementById("downloadBtn");
    button.innerText = "Download SVG";
    button.addEventListener("click", () => {
        const svgNode = svg.node();
        // 获取页面中所有的 <style> 标签内容
        const styleSheets = document.querySelectorAll("style");
        let styleContent = "";
        styleSheets.forEach(sheet => {
            styleContent += sheet.innerHTML;
        });

            // 创建一个 <style> 元素并添加到 SVG 的 <defs> 中
        const styleElement = document.createElementNS("http://www.w3.org/2000/svg", "style");
        styleElement.innerHTML = styleContent;
        svgNode.querySelector("defs")?.appendChild(styleElement) || svgNode.insertBefore(styleElement, svgNode.firstChild);

        const serializer = new XMLSerializer();
        const svgBlob = new Blob([serializer.serializeToString(svg.node())], {type: "image/svg+xml"});
        const url = URL.createObjectURL(svgBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "chart.svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

function getNodesByLevel(root){
    const levels = {};
    root.each(d => {
        if (!levels[d.depth]){
            levels[d.depth] = [];
        }
        levels[d.depth].push(d);
    });
    return levels;
}

function highlightPaths(bigRoot, smallTreeLevels){
    const queue = [bigRoot];
    bigRoot.isPathPoint = true;

    while (queue.length > 0){
        const currentNode = queue.shift();

        if(currentNode.parent && currentNode.parent.isPathPoint){
            const depth = currentNode.depth;
            const smallNodesAtDepth = smallTreeLevels[depth] || [];

            smallNodesAtDepth.forEach(smallNode => {
                if (currentNode.data.name === smallNode.data.name){
                    currentNode.isPathPoint = true;
                }
            })
        }

        // 子节点加入队列，进行层序遍历
        if(currentNode.children){
            currentNode.children.forEach(child => queue.push(child));
        }
    }
}

function downloadCSV(csv, filename) {
    let csvFile;
    let downloadLink;

    // 创建CSV文件
    csvFile = new Blob([csv], { type: 'text/csv' });

    // 创建下载链接
    downloadLink = document.createElement('a');

    // 文件名
    downloadLink.download = filename;

    // 创建链接
    downloadLink.href = window.URL.createObjectURL(csvFile);

    // 隐藏链接
    downloadLink.style.display = 'none';

    // 添加到页面并点击下载
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportTableToCSV(filename) {
    let csv = [];
    let rows = document.querySelectorAll("table tr");

    // 遍历表格的每一行
    for (let i = 0; i < rows.length; i++) {
        let cols = rows[i].querySelectorAll("td");
        // 遍历每一行的列
        for (let j = 0; j < cols.length; j++) {
            let row = cols[j].innerText.split(":");
            csv.push(row.join(";"));
        }
    }

    // 下载CSV文件
    downloadCSV(csv.join("\n"), filename);
}