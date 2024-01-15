class LocalStorageManager {
  constructor(key, maxSize) {
    this.key = key
    this.maxSize = maxSize || 50
    this.data = this.loadData()
  }

  // 加载本地存储数据
  loadData() {
    const storedData = localStorage.getItem(this.key)
    return storedData ? JSON.parse(storedData) : []
  }

  // 保存数据到本地存储
  saveData() {
    localStorage.setItem(this.key, JSON.stringify(this.data))
  }

  doubleDigit(num) {
    return num < 10 ? '0' + num : num.toString()
  }

  // 增加数据
  add(item) {
    const d = new Date()
    const date =
      d.getFullYear() +
      '-' +
      this.doubleDigit(d.getMonth() + 1) +
      '-' +
      this.doubleDigit(d.getDate()) +
      ' ' +
      this.doubleDigit(d.getHours()) +
      ':' +
      this.doubleDigit(d.getMinutes()) +
      ':' +
      this.doubleDigit(d.getSeconds())
    item.date = date

    this.data.push(item)

    // 如果数据超过最大限制，删除最早保存的数据
    if (this.data.length > this.maxSize) {
      this.data.shift()
    }

    this.saveData()
  }

  // 删除数据
  remove(index) {
    if (index >= 0 && index < this.data.length) {
      this.data.splice(index, 1)
      this.saveData()
    }
  }

  // 更新数据
  update(index, newItem) {
    if (index >= 0 && index < this.data.length) {
      this.data[index] = newItem
      this.saveData()
    }
  }

  // 获取所有数据
  getAll() {
    return this.data
  }

  // 获取特定位置的数据
  get(index) {
    return index >= 0 && index < this.data.length ? this.data[index] : null
  }

  // 清空本地存储
  clear() {
    localStorage.removeItem(this.key)
    this.data = []
  }
}

// 使用示例
const localStorageManager = new LocalStorageManager('myLocalStorageKey', 50)

export { localStorageManager as store }

// 添加数据，超过50条时会自动删除最早保存的数据
// for (let i = 1; i <= 60; i++) {
//   localStorageManager.add({ id: i, name: `Item ${i}` })
// }

// // 获取所有数据
// console.log(localStorageManager.getAll())

// // 添加数据
// localStorageManager.add({ id: 1, name: 'Item 1' })
// localStorageManager.add({ id: 2, name: 'Item 2' })

// // 获取所有数据
// console.log(localStorageManager.getAll())

// // 更新数据
// localStorageManager.update(0, { id: 1, name: 'Updated Item 1' })

// // 获取特定位置的数据
// console.log(localStorageManager.get(0))

// // 删除数据
// localStorageManager.remove(1)

// // 清空本地存储
// localStorageManager.clear()
