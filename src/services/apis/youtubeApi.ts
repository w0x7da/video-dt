const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL = "https://youtube-to-mp4.p.rapidapi.com/url";

export const youtubeApi = {
  async getVideoInfo(url: string) {
    const apiUrl = `${BASE_URL}?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      headers: {
        'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
        'x-rapidapi-key': RAPID_API_KEY
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      title: data.title || 'Vidéo YouTube',
      thumbnail: data.thumbnail || '',
      duration: data.duration || '00:00',
      platform: 'YouTube'
    };
  },

  async downloadVideo(url: string) {
    const apiUrl = `${BASE_URL}?url=${encodeURIComponent(url)}`;
    const response = await fetch(apiUrl, {
      headers: {
        'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
        'x-rapidapi-key': RAPID_API_KEY
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.url || '';
  }
};