const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL = "https://youtube-to-mp4.p.rapidapi.com";

export const youtubeApi = {
  async getVideoInfo(url: string) {
    try {
      console.log('Fetching video info for URL:', url);
      const encodedUrl = encodeURIComponent(url);
      const apiUrl = `${BASE_URL}/url?url=${encodedUrl}`;
      console.log('API URL:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      if (!response.ok) {
        console.error('API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);

      return {
        title: data.title || 'Vidéo YouTube',
        thumbnail: data.thumbnail || '',
        duration: data.duration || '00:00',
        platform: 'YouTube'
      };
    } catch (error) {
      console.error('Error in getVideoInfo:', error);
      throw error;
    }
  },

  async downloadVideo(url: string) {
    try {
      console.log('Downloading video for URL:', url);
      const encodedUrl = encodeURIComponent(url);
      const apiUrl = `${BASE_URL}/url?url=${encodedUrl}`;
      console.log('Download API URL:', apiUrl);

      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      if (!response.ok) {
        console.error('Download API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Download API Response data:', data);
      return data.url || '';
    } catch (error) {
      console.error('Error in downloadVideo:', error);
      throw error;
    }
  }
};