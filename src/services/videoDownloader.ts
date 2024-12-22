import axios from 'axios';

// Utilisation de l'API publique de cobalt
const BASE_URL = "https://co.wuk.sh/api/json";

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
      
      const response = await axios.post(BASE_URL, {
        url: url,
        vQuality: "best",
        isAudioOnly: false,
        isAudioMuted: false,
        dubLang: false
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

      return {
        title: response.data.meta?.title || 'Vidéo sans titre',
        thumbnail: response.data.thumb || '',
        duration: response.data.meta?.duration || '00:00',
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
      
      const response = await axios.post(BASE_URL, {
        url: url,
        vQuality: "best",
        isAudioOnly: false,
        isAudioMuted: false,
        dubLang: false
      });
      
      console.log('Download API Response:', response.data);

      if (response.data.error) {
        console.error('API returned error:', response.data.error);
        throw new Error(response.data.error);
      }

      if (!response.data.url) {
        console.error('No download URL available');
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Télécharger la vidéo
      console.log('Opening download URL:', response.data.url);
      window.open(response.data.url, '_blank');
      
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};