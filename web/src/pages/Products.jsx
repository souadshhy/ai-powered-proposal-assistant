import React from "react";
import { useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import Card from "../components/ui/Card.jsx";
import Empty from "../components/ui/Empty.jsx";
import ErrorBox from "../components/ui/ErrorBox.jsx";
import Input from "../components/forms/Input.jsx";
import PageHeader from "../components/layout/PageHeader.jsx";
import Pill from "../components/ui/Pill.jsx";
import ReadOnlyInput from "../components/forms/ReadOnlyInput.jsx";
import SearchBox from "../components/ui/SearchBox.jsx";
import TagList from "../components/ui/TagList.jsx";
import Toolbar from "../components/ui/Toolbar.jsx";
import useLoad from "../hooks/useLoad.js";
import { api, formatTry } from "../lib/api.js";
import { generateProductId } from "../utils/generators.js";

export default function Products() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const { data, loading, error, reload } = useLoad(
    () => api.products({ q, category, in_stock_only: false }),
    [q, category],
  );
  const products = data?.products || [];

  return (
    <>
      <PageHeader
        title="Ürünler"
        subtitle="Ürünleri listele, filtrele ve yeni ürün ekle."
        action={
          <button
            className="primary"
            onClick={() => setShowCreate(!showCreate)}
          >
            <Plus size={16} />
            Yeni Ürün
          </button>
        }
      />
      <Toolbar>
        <SearchBox
          value={q}
          onChange={setQ}
          placeholder="Ürün, alias, kategori ara"
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">Tüm kategoriler</option>
          <option value="barcode_scanner">Barcode scanner</option>
          <option value="pos_terminal">POS terminal</option>
          <option value="receipt_printer">Receipt printer</option>
          <option value="label_printer">Label printer</option>
          <option value="software_license">Software license</option>
          <option value="service">Service</option>
          <option value="accessory">Accessory</option>
        </select>
        <button onClick={reload}>
          <RefreshCw size={16} />
          Yenile
        </button>
      </Toolbar>
      {showCreate && (
        <ProductForm
          onCreated={() => {
            setShowCreate(false);
            reload();
          }}
        />
      )}
      <ErrorBox error={error} />
      {loading ? (
        <Empty text="Yükleniyor..." />
      ) : (
        <ProductTable products={products} />
      )}
    </>
  );
}

function ProductTable({ products }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Ürün</th>
            <th>Kategori</th>
            <th>Marka</th>
            <th>Fiyat</th>
            <th>Stok</th>
            <th>Etiketler</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.product_id}>
              <td>
                <strong>{product.name_tr}</strong>
                <small>
                  {product.product_id} · {product.sku}
                </small>
              </td>
              <td>{product.category}</td>
              <td>{product.brand}</td>
              <td>{formatTry(product.price_try)}</td>
              <td>
                <Pill tone={product.stock_qty > 0 ? "success" : "danger"}>
                  {product.stock_qty}
                </Pill>
              </td>
              <td>
                <TagList tags={product.tags} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductForm({ onCreated }) {
  const { data: productData } = useLoad(
    () => api.products({ in_stock_only: false }),
    [],
  );
  const existingProducts = productData?.products || [];
  const categories = useMemo(
    () =>
      [
        ...new Set(existingProducts.map((p) => p.category).filter(Boolean)),
      ].sort(),
    [existingProducts],
  );
  const existingTags = useMemo(
    () => [...new Set(existingProducts.flatMap((p) => p.tags || []))].sort(),
    [existingProducts],
  );

  const [aliasInput, setAliasInput] = useState("");
  const [alternativeSearch, setAlternativeSearch] = useState("");
  const [err, setErr] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [form, setForm] = useState(() => createProductDraft("accessory"));

  const updateCategory = (category) => {
    const product_id = generateProductId(category);
    setForm({
      ...form,
      category,
      product_id,
      sku: product_id.replace("PRD-", "TBR-"),
    });
  };

  const addAlias = () => {
    const value = aliasInput.trim();
    if (!value || form.aliases.tr.includes(value)) return;
    setForm({ ...form, aliases: { tr: [...form.aliases.tr, value] } });
    setAliasInput("");
  };

  const removeAlias = (value) =>
    setForm({
      ...form,
      aliases: { tr: form.aliases.tr.filter((alias) => alias !== value) },
    });
  const toggleTag = (tag) =>
    setForm({
      ...form,
      tags: form.tags.includes(tag)
        ? form.tags.filter((t) => t !== tag)
        : [...form.tags, tag],
    });
  const toggleAlternative = (productId) =>
    setForm({
      ...form,
      substitute_product_ids: form.substitute_product_ids.includes(productId)
        ? form.substitute_product_ids.filter((id) => id !== productId)
        : [...form.substitute_product_ids, productId],
    });

  const filteredAlternatives = existingProducts
    .filter((product) => {
      const text =
        `${product.product_id} ${product.name_tr} ${product.category}`.toLowerCase();
      return (
        product.product_id !== form.product_id &&
        text.includes(alternativeSearch.toLowerCase())
      );
    })
    .slice(0, 12);

  const validate = () => {
    const errors = {};
    if (!form.product_id)
      errors.product_id = "Product ID sistem tarafından üretilmelidir.";
    if (!form.sku) errors.sku = "SKU sistem tarafından üretilmelidir.";
    if (!form.name_tr.trim()) errors.name_tr = "Ürün adı zorunludur.";
    if (!form.category) errors.category = "Kategori seçilmelidir.";
    if (!form.brand.trim()) errors.brand = "Marka zorunludur.";
    if (!Number.isFinite(Number(form.price_try)) || Number(form.price_try) <= 0)
      errors.price_try = "Fiyat 0’dan büyük olmalıdır.";
    if (!Number.isInteger(Number(form.stock_qty)) || Number(form.stock_qty) < 0)
      errors.stock_qty = "Stok 0 veya daha büyük tam sayı olmalıdır.";
    if (
      !Number.isInteger(Number(form.warranty_months)) ||
      Number(form.warranty_months) < 0
    )
      errors.warranty_months = "Garanti ayı 0 veya daha büyük olmalıdır.";
    if (!form.notes.trim()) errors.notes = "Açıklama / not zorunludur.";
    if (!form.aliases.tr.length)
      errors.aliases = "En az bir Türkçe alias eklenmelidir.";
    if (!form.tags.length) errors.tags = "En az bir etiket seçilmelidir.";
    if (!form.substitute_product_ids.length)
      errors.substitute_product_ids = "En az bir alternatif ürün seçilmelidir.";
    return errors;
  };

  const submit = async (event) => {
    event.preventDefault();
    setErr("");
    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length) {
      setErr("Lütfen zorunlu alanları düzeltin.");
      return;
    }
    try {
      await api.createProduct(form);
      onCreated();
    } catch (error) {
      setErr(error.message);
    }
  };

  return (
    <Card>
      <h2>Yeni Ürün</h2>
      <p className="form-help">
        Tüm alanlar zorunludur. Hatalı veri girişini azaltmak için kategori,
        etiket ve alternatif ürünler mevcut değerlerden seçilir. Alias alanı
        arama kalitesini artırmak için düzenlenebilir.
      </p>
      <form className="form-grid" onSubmit={submit} noValidate>
        <ReadOnlyInput
          label="Product ID *"
          value={form.product_id}
          error={fieldErrors.product_id}
        />
        <ReadOnlyInput label="SKU *" value={form.sku} error={fieldErrors.sku} />
        <Input
          label="Ad *"
          value={form.name_tr}
          onChange={(value) => setForm({ ...form, name_tr: value })}
          error={fieldErrors.name_tr}
        />
        <label>
          Kategori *
          <select
            value={form.category}
            onChange={(e) => updateCategory(e.target.value)}
          >
            {categories.length ? (
              categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))
            ) : (
              <option value="accessory">accessory</option>
            )}
          </select>
          {fieldErrors.category && (
            <small className="field-error">{fieldErrors.category}</small>
          )}
        </label>
        <Input
          label="Marka *"
          value={form.brand}
          onChange={(value) => setForm({ ...form, brand: value })}
          error={fieldErrors.brand}
        />
        <Input
          label="Fiyat *"
          type="number"
          value={form.price_try}
          onChange={(value) => setForm({ ...form, price_try: Number(value) })}
          error={fieldErrors.price_try}
        />
        <Input
          label="Stok *"
          type="number"
          value={form.stock_qty}
          onChange={(value) => setForm({ ...form, stock_qty: Number(value) })}
          error={fieldErrors.stock_qty}
        />
        <Input
          label="Garanti Ayı *"
          type="number"
          value={form.warranty_months}
          onChange={(value) =>
            setForm({ ...form, warranty_months: Number(value) })
          }
          error={fieldErrors.warranty_months}
        />
        <label className="span2">
          Açıklama / Not *
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
          {fieldErrors.notes && (
            <small className="field-error">{fieldErrors.notes}</small>
          )}
        </label>

        <div className="span2 field-block">
          <label>Aliases TR *</label>
          <div className="chip-row">
            {form.aliases.tr.map((alias) => (
              <button
                type="button"
                className="chip"
                key={alias}
                onClick={() => removeAlias(alias)}
              >
                {alias} ×
              </button>
            ))}
          </div>
          <div className="inline-input">
            <input
              value={aliasInput}
              onChange={(e) => setAliasInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addAlias();
                }
              }}
              placeholder="Örn: kablosuz okuyucu"
            />
            <button type="button" onClick={addAlias}>
              Ekle
            </button>
          </div>
          {fieldErrors.aliases && (
            <small className="field-error">{fieldErrors.aliases}</small>
          )}
        </div>

        <div className="span2 field-block">
          <label>Etiketler *</label>
          <div className="selectable-grid">
            {existingTags.map((tag) => (
              <button
                type="button"
                key={tag}
                className={`select-chip ${form.tags.includes(tag) ? "selected" : ""}`}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
          {fieldErrors.tags && (
            <small className="field-error">{fieldErrors.tags}</small>
          )}
        </div>

        <div className="span2 field-block">
          <label>Alternatif Ürünler *</label>
          <input
            value={alternativeSearch}
            onChange={(e) => setAlternativeSearch(e.target.value)}
            placeholder="Ürün adı, ID veya kategori ara"
          />
          <div className="product-select-list">
            {filteredAlternatives.map((product) => (
              <button
                type="button"
                key={product.product_id}
                className={`product-option ${form.substitute_product_ids.includes(product.product_id) ? "selected" : ""}`}
                onClick={() => toggleAlternative(product.product_id)}
              >
                <span>
                  <strong>{product.name_tr}</strong>
                  <small>
                    {product.product_id} · {product.category}
                  </small>
                </span>
                <Pill tone={product.stock_qty > 0 ? "success" : "danger"}>
                  {product.stock_qty}
                </Pill>
              </button>
            ))}
          </div>
          {fieldErrors.substitute_product_ids && (
            <small className="field-error">
              {fieldErrors.substitute_product_ids}
            </small>
          )}
        </div>

        <button className="primary">Kaydet</button>
      </form>
      <ErrorBox error={err} />
    </Card>
  );
}

function createProductDraft(category) {
  const product_id = generateProductId(category);
  return {
    product_id,
    sku: product_id.replace("PRD-", "TBR-"),
    name_tr: "",
    category,
    brand: "TBR",
    price_try: 1000,
    stock_qty: 10,
    active: true,
    min_order_qty: 1,
    delivery_days: 2,
    warranty_months: 12,
    tags: [],
    aliases: { tr: [] },
    substitute_product_ids: [],
    notes: "",
  };
}
