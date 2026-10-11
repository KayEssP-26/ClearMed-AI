const apiBaseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options) {
  const response = await fetch(`${apiBaseUrl}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Something went wrong. Please try again.");
  }
  return response.json();
}

export function simplifyText(text) {
  return request("/simplify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function simplifyReport(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/simplify-report", { method: "POST", body: formData });
}
