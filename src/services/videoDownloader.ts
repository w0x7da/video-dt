const API_KEY = "d2ad8e0252msh7b0aebd45f1f0a6p1d1f15jsn965159d7c789";
const BASE_URL = "https://social-media-video-downloader-api.p.rapidapi.com/v1/social/video";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

interface Media {
  url: string;
  quality: string;
  extension: string;
  type: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      console.log('Fetching video info for URL:', url);
      const response = await fetch(`${BASE_URL}?url=${encodeURIComponent(url)}`, {
        method: 'GET',
        headers: {
          'X-RapidAPI-Key': API_KEY,
          'X-RapidAPI-Host': 'social-media-video-downloader-api.p.rapidapi.com'
        }
      });
      
      if (!response.ok) {
        console.error('API Response status:', response.status);
        console.error('API Response status text:', response.statusText);
        const errorText = await response.text();
        console.error('API Error response:', errorText);
        throw new Error(`Erreur API: ${response.status} - ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API Response data:', data);

      // Détecter la plateforme à partir de l'URL
      let platform = 'Inconnu';
      if (url.includes('instagram.com')) platform = 'Instagram';
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube';
      else if (url.includes('tiktok.com')) platform = 'TikTok';
      else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter';
      else if (url.includes('facebook.com') || url.includes('fb.watch')) platform = 'Facebook';

      // Extraire les informations de la réponse
      const videoData = data.data;
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
      const response = await fetch(`${BASE_URL}?url=${encodeURIComponent(url)}`, {
        method: 'GET',
        headers: {
          'X-RapidAPI-Key': API_KEY,
          'X-RapidAPI-Host': 'social-media-video-downloader-api.p.rapidapi.com'
        }
      });
      
      if (!response.ok) {
        console.error('Download API Response status:', response.status);
        console.error('Download API Response status text:', response.statusText);
        const errorText = await response.text();
        console.error('Download API Error response:', errorText);
        throw new Error(`Erreur API: ${response.status} - ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Download API Response:', data);
      
      const videoData = data.data;
      let downloadUrl = '';
      
      // Chercher la meilleure qualité disponible
      if (videoData.url) {
        downloadUrl = videoData.url;
      } else if (videoData.links && Array.isArray(videoData.links)) {
        const qualities = ['HD', 'high', 'medium', 'low'];
        for (const quality of qualities) {
          const link = videoData.links.find((l: any) => 
            l.quality?.toLowerCase() === quality.toLowerCase()
          );
          if (link?.url) {
            downloadUrl = link.url;
            break;
          }
        }
      }

      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      console.log('Download URL:', downloadUrl);

      // Télécharger la vidéo
      const videoResponse = await fetch(downloadUrl);
      const blob = await videoResponse.blob();
      
      // Créer un lien de téléchargement temporaire
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