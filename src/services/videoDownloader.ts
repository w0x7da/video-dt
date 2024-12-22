const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL = "https://zylalabs.com/api/5617/social+saver+api/7304";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      const response = await fetch(`${BASE_URL}/download+video?url=${encodeURIComponent(url)}`, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch video info');
      }
      
      const data = await response.json();
      console.log('API Response:', data);

      return {
        title: data.title || 'Vidéo sans titre',
        thumbnail: data.thumbnail || '',
        duration: data.duration || '00:00',
        platform: data.platform || 'Inconnu'
      };
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<string> {
    try {
      const response = await fetch(`${BASE_URL}/download+video?url=${encodeURIComponent(url)}`, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to download video');
      }
      
      const data = await response.json();
      console.log('Download Response:', data);
      
      if (data.downloadLink) {
        return data.downloadLink;
      } else {
        throw new Error('No download link available');
      }
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};