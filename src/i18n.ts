import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const resources = {
  en: {
    translation: {
      'getOne': 'Get on',
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
      'madeWithLove': 'Made with ♥️ by Walid 🙂‍↕️',
      'youtubeDT': 'Youtube DT on iPhone'
    }
  },
  fr: {
    translation: {
      'getOne': 'Obtenir sur',
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
      'madeWithLove': 'Fait avec ♥️ par Walid 🙂‍↕️',
      'youtubeDT': 'Youtube DT sur iPhone'
    }
  },
  es: {
    translation: {
      'getOne': 'Obtener en',
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
      'madeWithLove': 'Hecho con ♥️ por Walid 🙂‍↕️',
      'youtubeDT': 'Youtube DT en iPhone'
    }
  },
  it: {
    translation: {
      'getOne': 'Ottieni su',
      'videoDownloader': 'Scaricatore di Video',
      'pasteUrl': 'Incolla URL',
      'check': 'Verifica',
      'error': 'Errore',
      'invalidUrl': 'URL non valido',
      'unableToFetch': 'Impossibile recuperare le informazioni del video.',
      'downloadStarted': 'Il download è iniziato.',
      'unableToDownload': 'Impossibile scaricare il video.',
      'duration': 'Durata',
      'platform': 'Piattaforma',
      'madeWithLove': 'Fatto con ♥️ da Walid 🙂‍↕️',
      'youtubeDT': 'Youtube DT su iPhone'
    }
  },
  pt: {
    translation: {
      'getOne': 'Obter no',
      'videoDownloader': 'Baixador de Vídeos',
      'pasteUrl': 'Colar URL',
      'check': 'Verificar',
      'error': 'Erro',
      'invalidUrl': 'URL inválido',
      'unableToFetch': 'Não foi possível obter as informações do vídeo.',
      'downloadStarted': 'O download começou.',
      'unableToDownload': 'Não foi possível baixar o vídeo.',
      'duration': 'Duração',
      'platform': 'Plataforma',
      'madeWithLove': 'Feito com ♥️ por Walid 🙂‍↕️',
      'youtubeDT': 'Youtube DT no iPhone'
    }
  },
  ar: {
    translation: {
      'getOne': 'احصل على',
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
      'madeWithLove': 'صنع بـ ♥️ بواسطة وليد 🙂‍↕️',
      'youtubeDT': 'يوتيوب DT على آيفون'
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