package com.sportstv.mobile

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class CategoryAdapter(
    private var categories: List<String>,
    private val onCategorySelected: (String) -> Unit
) : RecyclerView.Adapter<CategoryAdapter.ViewHolder>() {

    private var selectedCategory: String = "All"

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvCategoryName: TextView = view.findViewById(R.id.tv_category_name)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_category_chip, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val category = categories[position]
        holder.tvCategoryName.text = category

        if (category == selectedCategory) {
            holder.tvCategoryName.setBackgroundResource(R.drawable.bg_category_chip)
            holder.tvCategoryName.setTextColor(0xFFFFFFFF.toInt()) // Highlight
            // Add a stroke programmatically or use a selected drawable
            holder.tvCategoryName.background.setTint(0xFF3B82F6.toInt()) // Neon Blue
        } else {
            holder.tvCategoryName.setBackgroundResource(R.drawable.bg_category_chip)
            holder.tvCategoryName.setTextColor(0xFFCBD5E1.toInt())
            holder.tvCategoryName.background.setTint(0xFF1E293B.toInt()) // Dark glass
        }

        holder.itemView.setOnClickListener {
            selectedCategory = category
            notifyDataSetChanged()
            onCategorySelected(category)
        }
    }

    override fun getItemCount() = categories.size

    fun updateCategories(newCategories: List<String>) {
        categories = newCategories
        if (!categories.contains(selectedCategory)) {
            selectedCategory = categories.firstOrNull() ?: "All"
        }
        notifyDataSetChanged()
    }
}
