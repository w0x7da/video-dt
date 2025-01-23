const COBALT_API = "https://api.cobalt.tools/v1";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

interface ApiResponse {
  status: string;
  text?: string;
  url?: string;
  thumb?: string;
  duration?: number;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      const response = await fetch(COBALT_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          aFormat: 'mp3',
          filenamePattern: 'basic',
          dubLang: false,
          vQuality: '1080'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      console.log('API Response:', data);

      if (data.status === 'error') {
        throw new Error(data.text || 'Une erreur est survenue');
      }

      // Détecter la plateforme à partir de l'URL
      let platform = 'Inconnu';
      if (url.includes('instagram.com')) platform = 'Instagram';
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube';
      else if (url.includes('tiktok.com')) platform = 'TikTok';
      else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter';
      else if (url.includes('facebook.com') || url.includes('fb.watch')) platform = 'Facebook';

      // Convertir la durée en format lisible
      let duration = '00:00';
      if (data.duration) {
        const minutes = Math.floor(data.duration / 60);
        const seconds = data.duration % 60;
        duration = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }

      return {
        title: data.text || 'Vidéo sans titre',
        thumbnail: data.thumb || '',
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
      const response = await fetch(COBALT_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          aFormat: 'mp3',
          filenamePattern: 'basic',
          dubLang: false,
          vQuality: '1080'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      console.log('Download Response:', data);

      if (data.status === 'error') {
        throw new Error(data.text || 'Une erreur est survenue');
      }

      if (!data.url) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Télécharger la vidéo
      const videoResponse = await fetch(data.url);
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