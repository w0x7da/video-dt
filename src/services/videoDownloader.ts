import axios from 'axios';
import axiosRetry from 'axios-retry';

// Configuration de l'API RapidAPI
const BASE_URL = "https://social-media-video-downloader.p.rapidapi.com/api/getSocialVideo";
const RAPID_API_KEY = "f9d117c6e1msh4f2a1bd09450f3dp1d7f87jsn0ce15135a0f9"; // Clé gratuite pour test
const RAPID_API_HOST = "social-media-video-downloader.p.rapidapi.com";

// Configure axios avec retry
const client = axios.create();
axiosRetry(client, { 
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || error.response?.status === 429;
  }
});

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
      
      const response = await client.get(BASE_URL, {
        params: { url },
        headers: {
          'X-RapidAPI-Key': RAPID_API_KEY,
          'X-RapidAPI-Host': RAPID_API_HOST
        },
        timeout: 15000
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
        title: videoData.title || 'Vidéo sans titre',
        thumbnail: videoData.thumbnail || '',
        duration: videoData.duration || '00:00',
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
      
      const response = await client.get(BASE_URL, {
        params: { url },
        headers: {
          'X-RapidAPI-Key': RAPID_API_KEY,
          'X-RapidAPI-Host': RAPID_API_HOST
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