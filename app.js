function logout() {
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Global utility for fetch error handling can be added here
async function apiPost(url, data) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (e) {
        console.error('API Error:', e);
        return {success: false, message: 'Network error'};
    }
}
