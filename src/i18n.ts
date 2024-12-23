import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      'getOne': 'Get one',
      'videoDownloader': 'Video Downloader',
      'pasteUrl': 'Paste video URL here',
      'check': 'Check',
      'download': 'Download',
      'duration': 'Duration',
      'platform': 'Platform',
      'downloadStarted': 'Download started',
      'error': 'Error',
      'invalidUrl': 'Please enter a valid URL',
      'unableToFetch': 'Unable to fetch video information',
      'unableToDownload': 'Unable to download video'
    }
  },
  fr: {
    translation: {
      'getOne': 'Obtenir',
      'videoDownloader': 'Téléchargeur de Vidéos',
      'pasteUrl': 'Collez l\'URL de la vidéo ici',
      'check': 'Vérifier',
      'download': 'Télécharger',
      'duration': 'Durée',
      'platform': 'Plateforme',
      'downloadStarted': 'Téléchargement démarré',
      'error': 'Erreur',
      'invalidUrl': 'Veuillez entrer une URL valide',
      'unableToFetch': 'Impossible de récupérer les informations de la vidéo',
      'unableToDownload': 'Impossible de télécharger la vidéo'
    }
  },
  es: {
    translation: {
      'getOne': 'Obtener',
      'videoDownloader': 'Descargador de Videos',
      'pasteUrl': 'Pega la URL del video aquí',
      'check': 'Verificar',
      'download': 'Descargar',
      'duration': 'Duración',
      'platform': 'Plataforma',
      'downloadStarted': 'Descarga iniciada',
      'error': 'Error',
      'invalidUrl': 'Por favor, introduce una URL válida',
      'unableToFetch': 'No se pudo obtener la información del video',
      'unableToDownload': 'No se pudo descargar el video'
    }
  },
  ar: {
    translation: {
      'getOne': 'احصل على واحد',
      'videoDownloader': 'تحميل الفيديو',
      'pasteUrl': 'الصق رابط الفيديو هنا',
      'check': 'تحقق',
      'download': 'تحميل',
      'duration': 'المدة',
      'platform': 'المنصة',
      'downloadStarted': 'بدأ التحميل',
      'error': 'خطأ',
      'invalidUrl': 'الرجاء إدخال رابط صحيح',
      'unableToFetch': 'تعذر جلب معلومات الفيديو',
      'unableToDownload': 'تعذر تحميل الفيديو'
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'fr',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;