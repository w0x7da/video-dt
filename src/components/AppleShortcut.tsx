import { Apple } from "lucide-react";
import { Button } from "./ui/button";
import { useTranslation } from "react-i18next";

export const AppleShortcut = () => {
  const { t } = useTranslation();
  
  return (
    <div className="mt-8">
      <a 
        href="https://www.icloud.com/shortcuts/a1aef2cda4964d47b846a5b941220535"
        target="_blank"
        rel="noopener noreferrer"
      >
        <Button 
          variant="outline" 
          className="bg-white hover:bg-gray-50 border-2"
        >
          {t('getOne')} <Apple className="ml-2" />
        </Button>
      </a>
    </div>
  );
};