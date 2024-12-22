const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/5393/universal+social+downloader+api/6986";

export const universalApi = {
  async fetchContent(url: string) {
    const apiUrl = `${BASE_URL}/download+social+media+content`;
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      },
      body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Universal API Error Response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
};