import { request } from "./client"

export async function getContributions() {
    return request<any>("/github/contributions")
}
