"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  children?: React.ReactNode;
  options?: Array<{ value: string; label: string }>;
  placeholder?: string;
}

const Select: React.FC<SelectProps> = ({ 
  value, 
  onValueChange, 
  className, 
  children,
  options,
  placeholder,
  ...props 
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onValueChange?.(e.target.value);
  };

  // Build options from children or options prop
  const renderOptions = () => {
    if (options) {
      return options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ));
    }
    return null;
  };

  return (
    <select
      value={value}
      onChange={handleChange}
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm ring-offset-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {renderOptions()}
      {children}
    </select>
  );
};
Select.displayName = "Select";

const SelectTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, children, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "flex h-10 w-full items-center justify-between rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm ring-offset-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  >
    {children}
  </button>
));
SelectTrigger.displayName = "SelectTrigger";

const SelectContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative z-50 min-w-[8rem] overflow-hidden rounded-md border bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5",
      className
    )}
    {...props}
  >
    {children}
  </div>
));
SelectContent.displayName = "SelectContent";

const SelectItem = React.forwardRef<
  HTMLOptionElement,
  React.OptionHTMLAttributes<HTMLOptionElement>
>(({ className, children, ...props }, ref) => (
  <option
    ref={ref}
    className={cn(
      "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-gray-700 focus:bg-gray-700",
      className
    )}
    {...props}
  >
    {children}
  </option>
));
SelectItem.displayName = "SelectItem";

const SelectValue = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement> & { placeholder?: string }
>(({ className, placeholder, ...props }, ref) => (
  <span
    ref={ref}
    className={cn("block truncate text-gray-400", className)}
    {...props}
  >
    {placeholder || props.children}
  </span>
));
SelectValue.displayName = "SelectValue";

export { Select, SelectTrigger, SelectContent, SelectItem, SelectValue };