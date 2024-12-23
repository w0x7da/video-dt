const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/5393/universal+social+downloader+api/6986";

export const universalApi = {
  async getVideoInfo(url: string) {
    const apiUrl = `${BASE_URL}/download+social+media+content`;
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      title: data.title || 'Vidéo',
      thumbnail: data.thumbnail || '',
      duration: data.duration || '00:00',
      platform: this.detectPlatform(url)
    };
  },

  async downloadVideo(url: string) {
    const apiUrl = `${BASE_URL}/download+social+media+content`;
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.downloadLink || '';
  },

  detectPlatform(url: string): string {
    if (url.includes('tiktok.com')) return 'TikTok';
    if (url.includes('facebook.com') || url.includes('fb.watch')) return 'Facebook';
    if (url.includes('twitter.com') || url.includes('x.com')) return 'Twitter';
    return 'Autre';
  }
};