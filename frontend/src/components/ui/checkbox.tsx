"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  label?: string;
  onCheckedChange?: (checked: boolean) => void;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, onCheckedChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onCheckedChange?.(e.target.checked);
    };

    return (
      <label className="inline-flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          ref={ref}
          className={cn(
            "h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0",
            className
          )}
          onChange={handleChange}
          {...props}
        />
        {label && <span className="text-sm text-gray-300">{label}</span>}
      </label>
    );
  }
);
Checkbox.displayName = "Checkbox";

export { Checkbox };