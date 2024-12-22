import axios from 'axios';

// Configuration de l'API
const BASE_URL = "https://ssyoutube.com/api/convert"; // API plus stable et rapide

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      console.log('Fetching video info for URL:', url);
      
      const response = await axios.get(`${BASE_URL}`, {
        params: {
          url: url
        },
        headers: {
          'Accept': 'application/json',
          'Origin': window.location.origin
        },
        timeout: 15000 // 15 secondes timeout
      });

      console.log('API Response:', response.data);

      // Détecter la plateforme à partir de l'URL
      let platform = 'Inconnu';
      if (url.includes('instagram.com')) platform = 'Instagram';
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube';
      else if (url.includes('tiktok.com')) platform = 'TikTok';
      else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter';
      else if (url.includes('facebook.com') || url.includes('fb.watch')) platform = 'Facebook';

      // Si la réponse contient une erreur
      if (response.data.error) {
        console.error('API returned error:', response.data.error);
        throw new Error(response.data.error);
      }

      const videoData = response.data;
      return {
        title: videoData.meta?.title || 'Vidéo sans titre',
        thumbnail: videoData.thumb || videoData.thumbnail || '',
        duration: videoData.meta?.duration || '00:00',
        platform
      };
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<void> {
    try {
      console.log('Starting video download for URL:', url);
      
      const response = await axios.get(`${BASE_URL}`, {
        params: {
          url: url
        },
        headers: {
          'Accept': 'application/json',
          'Origin': window.location.origin
        },
        timeout: 15000
      });
      
      console.log('Download API Response:', response.data);

      if (response.data.error) {
        console.error('API returned error:', response.data.error);
        throw new Error(response.data.error);
      }

      const downloadUrl = response.data.url || response.data.download_url;
      if (!downloadUrl) {
        console.error('No download URL available');
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Télécharger la vidéo
      console.log('Opening download URL:', downloadUrl);
      window.open(downloadUrl, '_blank');
      
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};