import axios from 'axios';
axios.defaults.xsrfHeaderName = "X-CSRFToken";


const argsToForm = (args) => {
    let data = new FormData()
    Object.keys(args).forEach((key) => {
        if (args.hasOwnProperty(key) && args[key] !== null && args[key] !== undefined) {
            data.append(key, args[key])
        }
    })
    return data
}

const http = (url, method, args, returnData = true) => {
    let data = args ? argsToForm(args) : undefined;
    let prefix = process.env.REACT_APP_API_URL;
    if (!prefix) {
        prefix = window.location.hostname === 'localhost'
            ? 'http://localhost:8000'
            : window.location.origin
    }
    return axios({
        method: method,
        url: prefix + url,
        data: data,
        withCredentials: false,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' }
    })
}

export { http as default }
