const canvas = document.getElementById('canvas')
const ctx = canvas.getContext('2d')
// const toggleButton = document.getElementById('toggleButton')

let scale // 初始缩放比例
let img
let imgX = 0 // 图片左上角 X 坐标
let imgY = 0 // 图片左上角 Y 坐标
let isDragging = false
let startDragX = 0
let startDragY = 0
let isMoveEnabled = true // 移动开关
let isDrawingMode = false // 绘制模式开关
let selectedRectIndex = -1 // 选中的长方形索引
let resizeHandleIndex = -1 // 选中的调整大小的手柄索引
let rectangles = [] // 存储绘制的长方形
const handleSize = 10 // 四角上小正方形的边长

// 加载图片
// img = new Image()
// img.src = 'assets/img/target1.jpg'

// // 图片加载完成后执行绘制
// img.onload = function () {
//   // 计算缩放比例，使图片刚好适应 canvas 尺寸
//   const widthRatio = canvas.width / img.width
//   const heightRatio = canvas.height / img.height
//   scale = Math.min(widthRatio, heightRatio)

//   // 让图片刚好居中显示在 canvas 中
//   imgX = (canvas.width - img.width * scale) / 2
//   imgY = (canvas.height - img.height * scale) / 2

//   drawImage()
// }

// 切换到【标靶设置】选项卡
function switchAndSetMarker() {
  // 加载 layui 的 element 模块
  const element = layui.element

  // 'tabN1'--选项卡的 lay-filter 属性；
  // 'setMarker'--选项卡标题的 lay-id 属性值
  element.tabChange('tabN1', 'setMarker')
}

// 绘制图片
function drawImage() {
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 计算绘制图片的尺寸
  const imageWidth = img.width * scale
  const imageHeight = img.height * scale

  // 使用 drawImage 方法绘制图片
  ctx.drawImage(img, imgX, imgY, imageWidth, imageHeight)

  // 绘制已保存的矩形
  ctx.strokeStyle = 'red'
  ctx.lineWidth = 2

  rectangles.forEach((rect, index) => {
    const rectX = imgX + rect.x * scale
    const rectY = imgY + rect.y * scale
    const rectWidth = rect.width * scale
    const rectHeight = rect.height * scale

    ctx.strokeRect(rectX, rectY, rectWidth, rectHeight)

    if (index === selectedRectIndex) {
      // 绘制选中长方形的4个小正方形
      const handles = [
        { x: rectX, y: rectY },
        { x: rectX + rectWidth, y: rectY },
        { x: rectX + rectWidth, y: rectY + rectHeight },
        { x: rectX, y: rectY + rectHeight }
      ]

      ctx.fillStyle = 'red'
      handles.forEach((handle, handleIndex) => {
        const halfSize = handleSize / 2
        ctx.fillRect(handle.x - halfSize, handle.y - halfSize, handleSize, handleSize)
        if (handleIndex % 2 === 0) {
          // 绘制调整大小的手柄
          ctx.fillRect(handle.x - halfSize, handle.y - halfSize, handleSize, handleSize)
        }
      })
    }
  })
}

// 更新 Canvas 的缩放
function updateScale(mouseX, mouseY) {
  // 计算鼠标在图片上的位置
  const mouseXInImage = (mouseX - imgX) / scale
  const mouseYInImage = (mouseY - imgY) / scale

  // 调整缩放比例
  scale += event.deltaY > 0 ? -0.05 : 0.05
  scale = Math.max(0.05, scale)

  // 更新图片位置，以鼠标位置为中心
  imgX = mouseX - mouseXInImage * scale
  imgY = mouseY - mouseYInImage * scale

  drawImage()
}

// 判断点是否在矩形内
function pointInsideRect(x, y, rect) {
  const rectX = imgX + rect.x * scale
  const rectY = imgY + rect.y * scale
  const rectWidth = rect.width * scale
  const rectHeight = rect.height * scale

  const halfSize = handleSize / 2

  return x >= rectX - halfSize && x <= rectX + rectWidth + halfSize && y >= rectY - halfSize && y <= rectY + rectHeight + halfSize
}

// 判断点是否在手柄内
function pointInsideHandle(x, y, handle) {
  const handleX = imgX + handle.x * scale
  const handleY = imgY + handle.y * scale
  const halfSize = handleSize / 2

  return x >= handleX - halfSize && x <= handleX + halfSize && y >= handleY - halfSize && y <= handleY + halfSize
}

// 获取鼠标在哪个矩形上
function getSelectedRectIndex(mouseX, mouseY) {
  for (let i = rectangles.length - 1; i >= 0; i--) {
    if (pointInsideRect(mouseX, mouseY, rectangles[i])) {
      return i
    }
  }
  return -1
}

// 获取鼠标在哪个手柄上
function getResizeHandleIndex(mouseX, mouseY) {
  if (selectedRectIndex > -1) {
    const rect = rectangles[selectedRectIndex]
    const handles = [
      { x: rect.x, y: rect.y },
      { x: rect.x + rect.width, y: rect.y },
      { x: rect.x + rect.width, y: rect.y + rect.height },
      { x: rect.x, y: rect.y + rect.height }
    ]

    for (let j = 0; j < handles.length; j++) {
      if (pointInsideHandle(mouseX, mouseY, handles[j])) {
        return { rectIndex: selectedRectIndex, handleIndex: j }
      }
    }
  }
  return -1
}

// 处理滚轮事件
function handleWheel(event) {
  event.preventDefault()

  if (isMoveEnabled || isDrawingMode) {
    updateScale(event.clientX, event.clientY)
  }
}

// 处理鼠标按下事件
function handleMouseDown(event) {
  if (isMoveEnabled) {
    isDragging = true
    startDragX = event.clientX
    startDragY = event.clientY
  } else if (isDrawingMode) {
    // 切换选中的长方形
    const mouseXInImage = event.clientX - canvas.getBoundingClientRect().left
    const mouseYInImage = event.clientY - canvas.getBoundingClientRect().top
    selectedRectIndex = getSelectedRectIndex(mouseXInImage, mouseYInImage)

    // 判断是否在手柄上
    if (selectedRectIndex > -1) {
      switchAndSetMarker()
      resizeHandleIndex = getResizeHandleIndex(mouseXInImage, mouseYInImage)
      if (resizeHandleIndex !== -1) {
        // 如果在手柄上，记录初始拖动位置
        isDragging = true
        startDragX = mouseXInImage - rectangles[resizeHandleIndex.rectIndex].x * scale
        startDragY = mouseYInImage - rectangles[resizeHandleIndex.rectIndex].y * scale
      } else {
        // 否则记录选中矩形的初始拖动位置
        isDragging = true
        startDragX = mouseXInImage - rectangles[selectedRectIndex].x * scale
        startDragY = mouseYInImage - rectangles[selectedRectIndex].y * scale
      }
    } else {
      // 只有在拖动时才绘制长方形
      const date = new Date()
      const id =
        date.getFullYear() +
        doubleDigit(date.getMonth() + 1) +
        doubleDigit(date.getDate()) +
        doubleDigit(date.getHours()) +
        doubleDigit(date.getMinutes()) +
        doubleDigit(date.getSeconds())
      const name = 'marker_' + id

      isDragging = true
      startDragX = (event.clientX - imgX) / scale
      startDragY = (event.clientY - imgY) / scale

      rectangles.push({
        id: id,
        name: name,
        x: startDragX,
        y: startDragY,
        width: 0,
        height: 0
      })
    }
  }
}

function doubleDigit(num) {
  return num < 10 ? '0' + num : num.toString()
}

// 处理鼠标移动事件
function handleMouseMove(event) {
  if (isDragging && isMoveEnabled) {
    const offsetX = event.clientX - startDragX
    const offsetY = event.clientY - startDragY

    // 根据鼠标拖动的偏移量调整图片位置
    imgX += offsetX
    imgY += offsetY

    drawImage()

    // 更新起始拖动位置
    startDragX = event.clientX
    startDragY = event.clientY
  } else if (isDragging && isDrawingMode) {
    // 更新当前绘制的矩形的大小
    const mouseXInImage = (event.clientX - imgX) / scale
    const mouseYInImage = (event.clientY - imgY) / scale

    if (resizeHandleIndex !== -1 && selectedRectIndex > -1) {
      // 如果在手柄上，调整大小
      const rect = rectangles[resizeHandleIndex.rectIndex]
      const handle = resizeHandleIndex.handleIndex

      if (handle === 0 || handle === 3) {
        rect.width -= mouseXInImage - rect.x
        rect.x = mouseXInImage
      }
      if (handle === 0 || handle === 1) {
        rect.height -= mouseYInImage - rect.y
        rect.y = mouseYInImage
      }
      if (handle === 1 || handle === 2) {
        rect.width = mouseXInImage - rect.x
      }
      if (handle === 2 || handle === 3) {
        rect.height = mouseYInImage - rect.y
      }
    } else if (selectedRectIndex > -1) {
      // 移动选中的长方形
      rectangles[selectedRectIndex].x = (event.clientX - canvas.getBoundingClientRect().left - startDragX) / scale
      rectangles[selectedRectIndex].y = (event.clientY - canvas.getBoundingClientRect().top - startDragY) / scale
    } else {
      // 更新当前绘制的矩形的大小
      rectangles[rectangles.length - 1].width = mouseXInImage - rectangles[rectangles.length - 1].x
      rectangles[rectangles.length - 1].height = mouseYInImage - rectangles[rectangles.length - 1].y
    }

    drawImage()
  }
}

// 处理鼠标释放事件
function handleMouseUp() {
  isDragging = false
  resizeHandleIndex = -1

  if (isDrawingMode) {
    // 结束绘制矩形
    drawImage()
    switchAndSetMarker()

    // 过滤掉宽高为 0 的 rect
    rectangles = rectangles.filter(rect => rect.width > 0 && rect.height > 0)
  }
}

// 处理右键菜单
function handleContextMenu(event) {
  event.preventDefault() // 阻止默认右键菜单
  const mouseXInImage = event.clientX - canvas.getBoundingClientRect().left
  const mouseYInImage = event.clientY - canvas.getBoundingClientRect().top
  selectedRectIndex = getSelectedRectIndex(mouseXInImage, mouseYInImage)

  if (selectedRectIndex > -1) {
    // If a rectangle is selected, show the delete menu
    showContextMenu(mouseXInImage, mouseYInImage)
  }
}

// 显示右键菜单
function showContextMenu(x, y) {
  const menu = document.createElement('div')
  menu.classList.add('context__menu')
  menu.style.position = 'absolute'
  menu.style.left = `${x}px`
  menu.style.top = `${y}px`
  menu.innerHTML = `
        <ul class="context">
          <li id="deleteMenuItem">删除</li>
        </ul>
      `

  document.body.appendChild(menu)

  // 添加事件监听
  // document.getElementById('editMenuItem').addEventListener('click', handleEditClick)
  document.getElementById('deleteMenuItem').addEventListener('click', handleDeleteClick)

  // 点击其他地方关闭上下文菜单
  window.addEventListener('click', handleOutsideClick)
}

// 处理删除事件
function handleDeleteClick() {
  if (selectedRectIndex > -1) {
    rectangles.splice(selectedRectIndex, 1)

    drawImage()
  }

  document.body.removeChild(document.querySelector('.context__menu'))
  window.removeEventListener('click', handleOutsideClick)
}

function handleOutsideClick(event) {
  const menu = document.querySelector('.context__menu')

  if (menu && !menu.contains(event.target)) {
    document.body.removeChild(menu)
    window.removeEventListener('click', handleOutsideClick)
  }
}

// 处理按钮点击事件
// toggleButton.addEventListener('click', function () {
//   isMoveEnabled = !isMoveEnabled
//   isDrawingMode = !isMoveEnabled
//   selectedRectIndex = -1
//   canvas.style.cursor = isMoveEnabled ? 'grab' : 'crosshair'
//   drawImage()
// })

// 监听滚轮事件
canvas.addEventListener('wheel', handleWheel)

// 监听鼠标按下事件
canvas.addEventListener('mousedown', handleMouseDown)
canvas.addEventListener('mousemove', handleMouseMove)
canvas.addEventListener('mouseup', handleMouseUp)
canvas.addEventListener('contextmenu', handleContextMenu)

// 初始绘制
// drawImage()
