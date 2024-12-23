import { Globe, RefreshCw } from "lucide-react";
import { Button } from "./ui/button";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const Header = () => {
  const navigate = useNavigate();
  const { i18n } = useTranslation();

  const languages = {
    en: { name: 'English', flag: '🇬🇧' },
    fr: { name: 'Français', flag: '🇫🇷' },
    es: { name: 'Español', flag: '🇪🇸' },
    ar: { name: 'العربية', flag: '🇸🇦' }
  };

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
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
      
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="hover:bg-secondary"
          >
            <Globe className="w-5 h-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {Object.entries(languages).map(([code, { name, flag }]) => (
            <DropdownMenuItem
              key={code}
              onClick={() => changeLanguage(code)}
              className="cursor-pointer"
            >
              <span className="mr-2">{flag}</span>
              {name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
};