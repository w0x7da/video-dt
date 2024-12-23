import { Smartphone } from "lucide-react";
import { Button } from "./ui/button";
import { useTranslation } from "react-i18next";

export const AppleShortcut = () => {
  const { t } = useTranslation();
  
  return (
    <div className="mt-8 flex justify-center">
      <a 
        href="https://www.icloud.com/shortcuts/a1aef2cda4964d47b846a5b941220535"
        target="_blank"
        rel="noopener noreferrer"
      >
        <Button 
          className="bg-black hover:bg-gray-800 text-white border-none"
        >
          {t('getOne')} iPhone <Smartphone className="ml-2" />
        </Button>
      </a>
    </div>
  );
};