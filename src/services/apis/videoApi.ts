const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/5789/video+downloader+api/7526";

export const videoApi = {
  async fetchContent(url: string) {
    const apiUrl = `${BASE_URL}/download+media?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Video API Error Response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
};