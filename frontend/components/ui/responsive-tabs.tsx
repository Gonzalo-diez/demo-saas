"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LucideIcon } from "lucide-react";

export type TabItem = {
  value: string;
  label: string;
  icon: LucideIcon;
  content: React.ReactNode;
};

type ResponsiveTabsProps = {
  tabs: TabItem[];
  activeTab: string;
  onTabChange: (value: string) => void;
  tabsListClassName?: string;
};

export function ResponsiveTabs({
  tabs,
  activeTab,
  onTabChange,
  tabsListClassName = `sm:max-w-md sm:grid-cols-${tabs.length}`,
}: ResponsiveTabsProps) {
  return (
    <Tabs value={activeTab} onValueChange={onTabChange} className="w-full">
      <div className="sm:hidden">
        <Select value={activeTab} onValueChange={onTabChange}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {tabs.map(({ value, label, icon: Icon }) => (
              <SelectItem key={value} value={value}>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {label}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <TabsList className={`hidden sm:grid sm:w-full ${tabsListClassName}`}>
        {tabs.map(({ value, label, icon: Icon }) => (
          <TabsTrigger key={value} value={value}>
            <Icon className="mr-2 h-4 w-4" />
            {label}
          </TabsTrigger>
        ))}
      </TabsList>

      {tabs.map(({ value, content }) => (
        <TabsContent key={value} value={value} className="mt-6">
          {content}
        </TabsContent>
      ))}
    </Tabs>
  );
}