const canvas = document.getElementById('canvas')
const ctx = canvas.getContext('2d')
const rectangles = []
let isDrawing = false
let isDragging = false
let isResizing = false
let selectedRectangle = null
let offsetX = 0
let offsetY = 0
let resizeHandleSize = 12
let resizingHandleIndex = -1 // 记录调整大小的手柄索引

function drawRectangle(x, y, width, height) {
  ctx.strokeStyle = 'red'
  ctx.lineWidth = 2
  ctx.strokeRect(x, y, width, height)
}

function drawResizeHandles(x, y, width, height) {
  const halfSize = resizeHandleSize / 2
  // const halfSize = 0

  ctx.fillStyle = 'red'
  // 左上角
  ctx.fillRect(x - halfSize, y - halfSize, resizeHandleSize, resizeHandleSize)
  // 右上角
  ctx.fillRect(x + width - halfSize, y - halfSize, resizeHandleSize, resizeHandleSize)
  // 左下角
  ctx.fillRect(x - halfSize, y + height - halfSize, resizeHandleSize, resizeHandleSize)
  // 右下角
  ctx.fillRect(x + width - halfSize, y + height - halfSize, resizeHandleSize, resizeHandleSize)
}

function clearCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

function findRectangle(x, y) {
  const halfSize = resizeHandleSize / 2
  return rectangles.find(
    rectangle =>
      x >= rectangle.x - halfSize &&
      x <= rectangle.x + rectangle.width + halfSize &&
      y >= rectangle.y - halfSize &&
      y <= rectangle.y + rectangle.height + halfSize
  )
}

// 切换到【标靶设置】选项卡
function switchAndSetMarker() {
  // 加载 layui 的 element 模块
  const element = layui.element

  // 'tabN1'--选项卡的 lay-filter 属性；
  // 'setMarker'--选项卡标题的 lay-id 属性值
  element.tabChange('tabN1', 'setMarker')
}

function handleMouseDown(event) {
  resizingHandleIndex = -1
  const x = event.clientX - canvas.getBoundingClientRect().left
  const y = event.clientY - canvas.getBoundingClientRect().top

  if (event.button === 0) {
    selectedRectangle = findRectangle(x, y)
    // console.log('MouseDown selectedRectangle', selectedRectangle)

    if (selectedRectangle) {
      switchAndSetMarker()
      const resizeHandles = calculateResizeHandles(selectedRectangle)
      resizingHandleIndex = -1

      // Check if the mouse is inside any of the resize handles
      for (let i = 0; i < resizeHandles.length; i++) {
        const handle = resizeHandles[i]
        if (x >= handle.x && x <= handle.x + resizeHandleSize && y >= handle.y && y <= handle.y + resizeHandleSize) {
          resizingHandleIndex = i
          break
        }
      }

      if (resizingHandleIndex >= 0) {
        isResizing = true
        offsetX = x
        offsetY = y
      } else {
        isDragging = true
        offsetX = x - selectedRectangle.x
        offsetY = y - selectedRectangle.y

        // Remove resize handles from other rectangles
        clearCanvas()
        rectangles.forEach(rect => {
          if (rect !== selectedRectangle) {
            rect.showHandles = false
          }
        })
      }
    } else {
      isDrawing = true
      offsetX = x
      offsetY = y

      // Remove resize handles from other rectangles
      clearCanvas()
      rectangles.forEach(rect => {
        rect.showHandles = false
      })
    }
  }
}

function handleMouseMove(event) {
  const x = event.clientX - canvas.getBoundingClientRect().left
  const y = event.clientY - canvas.getBoundingClientRect().top

  if (isDragging) {
    selectedRectangle.x = x - offsetX
    selectedRectangle.y = y - offsetY
    clearCanvas()
    rectangles.forEach(rectangle => drawRectangle(rectangle.x, rectangle.y, rectangle.width, rectangle.height))
    drawResizeHandles(selectedRectangle.x, selectedRectangle.y, selectedRectangle.width, selectedRectangle.height)
    switchAndSetMarker()
  } else if (isResizing) {
    // console.log('mouseMove', x, y, offsetX, offsetY)
    const deltaX = x - offsetX
    const deltaY = y - offsetY

    switch (resizingHandleIndex) {
      case 0: // 左上角
        selectedRectangle.x += deltaX
        selectedRectangle.y += deltaY
        selectedRectangle.width -= deltaX
        selectedRectangle.height -= deltaY
        break
      case 1: // 右上角
        selectedRectangle.y += deltaY
        selectedRectangle.width += deltaX
        selectedRectangle.height -= deltaY
        break
      case 2: // 左下角
        selectedRectangle.x += deltaX
        selectedRectangle.width -= deltaX
        selectedRectangle.height += deltaY
        break
      case 3: // 右下角
        selectedRectangle.width += deltaX
        selectedRectangle.height += deltaY
        break
    }

    clearCanvas()
    rectangles.forEach(rectangle => drawRectangle(rectangle.x, rectangle.y, rectangle.width, rectangle.height))
    drawResizeHandles(selectedRectangle.x, selectedRectangle.y, selectedRectangle.width, selectedRectangle.height)
    switchAndSetMarker()

    offsetX = x
    offsetY = y
  } else if (isDrawing) {
    clearCanvas()
    const width = x - offsetX
    const height = y - offsetY
    drawRectangle(offsetX, offsetY, width, height)
  }
}

function handleMouseUp() {
  if (isDrawing || isDragging || isResizing) {
    isDrawing = false
    isDragging = false
    isResizing = false

    if (!selectedRectangle && !isDrawing) {
      const x = event.clientX - canvas.getBoundingClientRect().left
      const y = event.clientY - canvas.getBoundingClientRect().top
      const width = x - offsetX
      const height = y - offsetY

      storeRectangle({ x: offsetX, y: offsetY, width: Math.abs(width), height: Math.abs(height) })
      clearCanvas()
      rectangles.forEach(rectangle => drawRectangle(rectangle.x, rectangle.y, rectangle.width, rectangle.height))
    }
  }
}

function storeRectangle(rect) {
  const date = new Date()
  const id =
    date.getFullYear() +
    doubleDigit(date.getMonth() + 1) +
    doubleDigit(date.getDate()) +
    doubleDigit(date.getHours()) +
    doubleDigit(date.getMinutes()) +
    doubleDigit(date.getSeconds())
  const name = 'marker_' + id
  rect.id = id
  rect.name = name
  rectangles.push(rect)
  console.log('rectangles', rectangles, selectedRectangle)
}

function doubleDigit(num) {
  return num < 10 ? '0' + num : num.toString()
}

function calculateResizeHandles(rectangle) {
  const handles = []
  handles.push({ x: rectangle.x - resizeHandleSize / 2, y: rectangle.y - resizeHandleSize / 2 })
  handles.push({ x: rectangle.x + rectangle.width - resizeHandleSize / 2, y: rectangle.y - resizeHandleSize / 2 })
  handles.push({ x: rectangle.x - resizeHandleSize / 2, y: rectangle.y + rectangle.height - resizeHandleSize / 2 })
  handles.push({ x: rectangle.x + rectangle.width - resizeHandleSize / 2, y: rectangle.y + rectangle.height - resizeHandleSize / 2 })
  return handles
}

function handleContextMenu(event) {
  event.preventDefault() // 阻止默认右键菜单

  const x = event.clientX - canvas.getBoundingClientRect().left
  const y = event.clientY - canvas.getBoundingClientRect().top

  selectedRectangle = findRectangle(x, y)

  if (selectedRectangle) {
    showContextMenu(x, y)
  }
}

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

function handleOutsideClick(event) {
  const menu = document.querySelector('.context__menu')

  if (menu && !menu.contains(event.target)) {
    document.body.removeChild(menu)
    window.removeEventListener('click', handleOutsideClick)
  }
}

function handleEditClick() {
  // 在这里执行编辑操作
  document.body.removeChild(document.querySelector('.context__menu'))
  window.removeEventListener('click', handleOutsideClick)
}

function handleDeleteClick() {
  if (selectedRectangle) {
    const index = rectangles.indexOf(selectedRectangle)
    rectangles.splice(index, 1)
    clearCanvas()
    rectangles.forEach(rectangle => drawRectangle(rectangle.x, rectangle.y, rectangle.width, rectangle.height))
  }

  document.body.removeChild(document.querySelector('.context__menu'))
  window.removeEventListener('click', handleOutsideClick)
}

function render() {
  rectangles.forEach(rectangle => {
    drawRectangle(rectangle.x, rectangle.y, rectangle.width, rectangle.height)

    if (rectangle === selectedRectangle) {
      drawResizeHandles(rectangle.x, rectangle.y, rectangle.width, rectangle.height)
    } else if (rectangle.showHandles) {
      drawResizeHandles(rectangle.x, rectangle.y, rectangle.width, rectangle.height)
    }
  })

  requestAnimationFrame(render)
}

canvas.addEventListener('mousedown', handleMouseDown)
canvas.addEventListener('mousemove', handleMouseMove)
canvas.addEventListener('mouseup', handleMouseUp)
canvas.addEventListener('contextmenu', handleContextMenu)

render()
