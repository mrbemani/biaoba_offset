/**************
 * 封装数据请求 *
 **************/
class DataRequest {
  constructor(baseUrl) {
    this.baseUrl = baseUrl
  }

  async get(endpoint, queryParams = {}) {
    try {
      const url = new URL(endpoint, this.baseUrl)
      if (Object.keys(queryParams).length > 0) {
        url.search = new URLSearchParams(queryParams)
      }

      const response = await fetch(url.toString())
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      return response.json()
    } catch (error) {
      throw new Error(`An error occurred while fetching data: ${error.message}`)
    }
  }

  async post(endpoint, data) {
    try {
      const url = new URL(endpoint, this.baseUrl)

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      return response.json()
    } catch (error) {
      throw new Error(`An error occurred while posting data: ${error.message}`)
    }
  }
}

// 设置 baseUrl，这里设置为当前页面的地址
// 注意：生产环境请设置为实际的 API 接口地址
const baseUrl = location.protocol + '//' + location.host
export const api = new DataRequest(baseUrl)

// --------------------------------------------------
/*************
 * post 用例 *
 *************/

// const postData = {
//   objectID: 'ee839ae27a1411ee807672df0b62c6a6'
// }

// api
//   .post('/api/v1/projectors/set/', postData)
//   .then(data => {
//     console.log(data)
//   })
//   .catch(error => {
//     console.error(error)
//   })
// --------------------------------------------------
