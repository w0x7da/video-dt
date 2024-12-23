import { youtubeApi } from './apis/youtubeApi';
import { instagramApi } from './apis/instagramApi';
import { universalApi } from './apis/universalApi';

export interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        return await youtubeApi.getVideoInfo(url);
      } else if (url.includes('instagram.com')) {
        return await instagramApi.getVideoInfo(url);
      } else {
        return await universalApi.getVideoInfo(url);
      }
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<void> {
    try {
      let downloadUrl = '';
      let filename = `video_${Date.now()}.mp4`;
      
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        downloadUrl = await youtubeApi.downloadVideo(url);
      } else if (url.includes('instagram.com')) {
        downloadUrl = await instagramApi.downloadVideo(url);
      } else {
        downloadUrl = await universalApi.downloadVideo(url);
      }

      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Créer un lien <a> et simuler un clic pour déclencher le téléchargement
      const downloadElement = document.createElement('a');
      downloadElement.href = downloadUrl;
      downloadElement.download = filename;
      downloadElement.target = '_blank'; // Ouvrir dans un nouvel onglet
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};