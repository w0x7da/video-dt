import axios from 'axios';

// Utilisation de l'API publique de yt-dlp
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
        aFormat: "mp3",
        filenamePattern: "basic",
        dubLang: false,
        vQuality: "1080"
      });

      console.log('API Response:', response.data);

      // Détecter la plateforme à partir de l'URL
      let platform = 'Inconnu';
      if (url.includes('instagram.com')) platform = 'Instagram';
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube';
      else if (url.includes('tiktok.com')) platform = 'TikTok';
      else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter';
      else if (url.includes('facebook.com') || url.includes('fb.watch')) platform = 'Facebook';

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
        aFormat: "mp4",
        filenamePattern: "basic",
        dubLang: false,
        vQuality: "1080"
      });
      
      console.log('Download API Response:', response.data);

      if (!response.data.url) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Télécharger la vidéo
      const videoResponse = await axios.get(response.data.url, {
        responseType: 'blob'
      });
      
      // Créer un lien de téléchargement temporaire
      const blob = new Blob([videoResponse.data], { type: 'video/mp4' });
      const downloadElement = document.createElement('a');
      downloadElement.href = URL.createObjectURL(blob);
      
      // Générer un nom de fichier basé sur la plateforme
      const platform = url.includes('instagram.com') ? 'instagram' :
                      url.includes('youtube.com') || url.includes('youtu.be') ? 'youtube' :
                      url.includes('tiktok.com') ? 'tiktok' :
                      url.includes('twitter.com') || url.includes('x.com') ? 'twitter' :
                      url.includes('facebook.com') || url.includes('fb.watch') ? 'facebook' : 'video';
      
      downloadElement.download = `${platform}_${Date.now()}.mp4`;
      
      // Déclencher le téléchargement
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
      
      // Nettoyer l'URL temporaire
      URL.revokeObjectURL(downloadElement.href);
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};