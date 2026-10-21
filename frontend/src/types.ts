export type Product={id:number;code:string;name:string;category:string;price_cents:number;minimum_stock:number;active:boolean;stock:number;low_stock:boolean};
export type Movement={id:number;product_id:number;product_name:string;quantity:number;kind:string;reason:string;occurred_at:string;sale_id:number|null};
export type Sale={id:number;occurred_at:string;total_cents:number;canceled_at:string|null;items:{product_id:number;product_name:string;quantity:number;unit_price_cents:number;subtotal_cents:number}[]};
export type Dashboard={revenue_cents:number;sales_count:number;average_ticket_cents:number;daily:{date:string;revenue_cents:number}[];categories:{category:string;revenue_cents:number}[];top_products:{product_id:number;name:string;quantity:number}[];low_stock:Product[]};
