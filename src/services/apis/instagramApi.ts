const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/2883/instagram+photo+and+video+saver+api/3005";

export const instagramApi = {
  async getVideoInfo(url: string) {
    const apiUrl = `${BASE_URL}/content+downloader?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      title: data.title || data.caption || 'Vidéo Instagram',
      thumbnail: data.thumbnail || data.cover || '',
      duration: data.duration || '00:00',
      platform: 'Instagram'
    };
  },

  async downloadVideo(url: string) {
    const apiUrl = `${BASE_URL}/content+downloader?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.downloadLink || data.download_url || '';
  }
};