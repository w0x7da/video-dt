const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/2883/instagram+photo+and+video+saver+api/3005";

export const instagramApi = {
  async fetchContent(url: string) {
    const apiUrl = `${BASE_URL}/content+downloader?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Instagram API Error Response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
};