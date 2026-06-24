"use client";
import { motion } from "framer-motion";
import { Card } from "./card";

export function KpiStat({ label, value, suffix }: { label: string; value: string; suffix?: string }) {
  return (
    <Card className="p-5">
      <div className="text-sm text-muted-foreground">{label}</div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="mt-1 text-2xl font-semibold"
      >
        {value}
        {suffix ? <span className="text-base text-muted-foreground"> {suffix}</span> : null}
      </motion.div>
    </Card>
  );
}
