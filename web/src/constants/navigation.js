import { Activity, Boxes, BookOpen, ClipboardList, LayoutDashboard, TerminalSquare } from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'products', label: 'Ürünler', icon: Boxes },
  { id: 'knowledge', label: 'Bilgi Kayıtları', icon: BookOpen },
  { id: 'quotes', label: 'Teklifler', icon: ClipboardList },
  { id: 'logs', label: 'Tool Logları', icon: TerminalSquare },
  { id: 'sessions', label: 'Sohbet Oturumları', icon: Activity },
];
