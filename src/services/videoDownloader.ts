import { instagramApi } from './apis/instagramApi';
import { universalApi } from './apis/universalApi';
import { grabberApi } from './apis/grabberApi';
import { videoApi } from './apis/videoApi';
import { detectPlatform } from './utils/platformDetector';
import { createDownloadLink, findBestQualityUrl } from './utils/downloadHelper';

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
      
      let data;
      const platform = detectPlatform(url);
      
      if (platform === 'Instagram') {
        data = await instagramApi.fetchContent(url);
      } else {
        try {
          data = await universalApi.fetchContent(url);
        } catch (error) {
          console.log('Universal API failed, trying Video API');
          try {
            data = await videoApi.fetchContent(url);
          } catch (videoError) {
            console.log('Video API failed, trying Grabber API');
            data = await grabberApi.fetchContent(url);
          }
        }
      }

      console.log('API Response:', data);

      if (data.error) {
        console.error('API Error:', data.error);
        throw new Error(data.error);
      }

      let duration = data.duration || data.Duration || '00:00';
      if (typeof duration === 'number') {
        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);
        duration = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }

      return {
        title: data.title || data.Title || data.caption || data.description || 'Vidéo sans titre',
        thumbnail: data.thumbnail || data.Thumbnail || data.cover || data.thumbnail_url || '',
        duration,
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
      
      let data;
      const platform = detectPlatform(url);
      
      if (platform === 'Instagram') {
        data = await instagramApi.fetchContent(url);
      } else {
        try {
          data = await universalApi.fetchContent(url);
        } catch (error) {
          console.log('Universal API failed, trying Video API');
          try {
            data = await videoApi.fetchContent(url);
          } catch (videoError) {
            console.log('Video API failed, trying Grabber API');
            data = await grabberApi.fetchContent(url);
          }
        }
      }

      console.log('Download Response:', data);
      
      if (data.error) {
        console.error('API Error:', data.error);
        throw new Error(data.error);
      }

      const downloadUrl = findBestQualityUrl(data);
      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      console.log('Starting download from URL:', downloadUrl);

      // Utiliser un proxy CORS pour le téléchargement
      const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(downloadUrl)}`;
      const videoResponse = await fetch(proxyUrl);
      
      if (!videoResponse.ok) {
        throw new Error(`Erreur lors du téléchargement de la vidéo: ${videoResponse.status}`);
      }

      const blob = await videoResponse.blob();
      if (blob.size === 0) {
        throw new Error('Le fichier téléchargé est vide');
      }
      
      const downloadUrl2 = createDownloadLink(blob, platform);
      const downloadElement = document.createElement('a');
      downloadElement.href = downloadUrl2;
      
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
      
      URL.revokeObjectURL(downloadUrl2);

      console.log('Download completed successfully');
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};