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
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data);

      // Vérification plus approfondie de la réponse
      if (data.error) {
        throw new Error(data.error);
      }

      return {
        title: data.title || data.Title || 'Vidéo sans titre',
        thumbnail: data.thumbnail || data.Thumbnail || '',
        duration: data.duration || data.Duration || '00:00',
        platform: data.platform || data.Platform || 'Inconnu'
      };
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<string> {
    try {
      const response = await fetch(`${BASE_URL}/download+video?url=${encodeURIComponent(url)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Download Response:', data);
      
      const downloadLink = data.downloadLink || data.DownloadLink || data.url || data.URL;
      if (downloadLink) {
        return downloadLink;
      } else {
        throw new Error('Aucun lien de téléchargement disponible');
      }
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};