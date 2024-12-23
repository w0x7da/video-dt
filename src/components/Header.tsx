import { Globe, RefreshCw } from "lucide-react";
import { Button } from "./ui/button";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

export const Header = () => {
  const navigate = useNavigate();
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'fr' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <header className="w-full flex justify-between items-center p-4">
      <button 
        onClick={() => window.location.reload()} 
        className="text-xl font-bold flex items-center gap-2 hover:opacity-80 transition-opacity"
      >
        <RefreshCw className="w-5 h-5" />
        DT Vidéo
      </button>
      
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleLanguage}
        className="hover:bg-secondary"
      >
        <Globe className="w-5 h-5" />
      </Button>
    </header>
  );
};