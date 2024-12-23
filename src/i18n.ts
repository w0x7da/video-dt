import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const resources = {
  en: {
    translation: {
      'videoDownloader': 'Video Downloader',
      'pasteUrl': 'Paste URL',
      'check': 'Check',
      'error': 'Error',
      'invalidUrl': 'Invalid URL',
      'unableToFetch': 'Unable to fetch video information.',
      'downloadStarted': 'Download has started.',
      'unableToDownload': 'Unable to download the video.',
      'duration': 'Duration',
      'platform': 'Platform',
    }
  },
  fr: {
    translation: {
      'videoDownloader': 'Téléchargeur de vidéos',
      'pasteUrl': 'Coller l\'URL',
      'check': 'Vérifier',
      'error': 'Erreur',
      'invalidUrl': 'URL invalide',
      'unableToFetch': 'Impossible de récupérer les informations vidéo.',
      'downloadStarted': 'Le téléchargement a commencé.',
      'unableToDownload': 'Impossible de télécharger la vidéo.',
      'duration': 'Durée',
      'platform': 'Plateforme',
    }
  },
  es: {
    translation: {
      'videoDownloader': 'Descargador de videos',
      'pasteUrl': 'Pegar URL',
      'check': 'Verificar',
      'error': 'Error',
      'invalidUrl': 'URL inválida',
      'unableToFetch': 'No se pudo obtener la información del video.',
      'downloadStarted': 'La descarga ha comenzado.',
      'unableToDownload': 'No se pudo descargar el video.',
      'duration': 'Duración',
      'platform': 'Plataforma',
    }
  },
  ar: {
    translation: {
      'videoDownloader': 'محمل الفيديو',
      'pasteUrl': 'الصق الرابط',
      'check': 'تحقق',
      'error': 'خطأ',
      'invalidUrl': 'رابط غير صالح',
      'unableToFetch': 'تعذر الحصول على معلومات الفيديو.',
      'downloadStarted': 'بدأ التنزيل.',
      'unableToDownload': 'تعذر تنزيل الفيديو.',
      'duration': 'المدة',
      'platform': 'المنصة',
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'fr', // default language
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;