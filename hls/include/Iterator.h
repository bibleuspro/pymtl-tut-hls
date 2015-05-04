#ifndef ITERATOR_H
#define ITERATOR_H

#include "ItuIface.h"
#include "ap_utils.h"

template<typename T> class ReferenceProxy;
template<typename T> class _iterator;

extern volatile ItuIfaceType g_itu_iface;

//-------------------------------------------------------------------
// Class ReferenceProxy
//-------------------------------------------------------------------
template<typename T>
class ReferenceProxy {
  friend class _iterator<T>;

  private:
    // data structure id
    unsigned m_ds_id;

    // index to an data element
    int      m_index;

  public:

    ReferenceProxy() : m_ds_id( 0 ), m_index( 0 ) {}
    ReferenceProxy( unsigned ds_id, int index )
      : m_ds_id( ds_id ), m_index( index ) {}
    //ReferenceProxy( unsigned ds_id, int index, volatile ItuIfaceType* iface )
    //  : m_ds_id( ds_id ), m_index( index ), m_itu_iface(iface) {}

    ~ReferenceProxy(){}

    operator T() const
    {
      //#pragma HLS INLINE self off
      //send a read request
      ItuRespType resp = itu_read (g_itu_iface, m_ds_id, m_index);
      T data = resp & 0xFFFF;
      return data;
    }

    ReferenceProxy& operator=( T data )
    {
      //#pragma HLS INLINE self off
      //send a write request
      int idata = data & 0xFFFF;
      ItuRespType resp = itu_write (g_itu_iface, m_ds_id, m_index, idata);
      // verify first bit of resp is 1?
      return *this;
    }

    ReferenceProxy& operator=( const ReferenceProxy& x )
    {
      return operator=( static_cast<T>( x ) );
    }

}; // class ReferenceProxy

//-------------------------------------------------------------------
// Class _iterator
//-------------------------------------------------------------------
template<typename T>
class _iterator {

  public:
    //typedef std::random_access_iterator_tag   iterator_category;
    //typedef ptrdiff_t                         difference_type;
    typedef T                                 value_type;
    typedef _iterator                         pointer;
    typedef ReferenceProxy<T>                 reference;
    
  private:
    // data structure id
    unsigned m_ds_id;

    // index to an data element
    unsigned m_index;

    //
    //static ItuIfaceType m_iface;

  public:

    //--------------------------------------------------------------
    //  constructors
    //--------------------------------------------------------------

    // default constructor
    _iterator() : m_ds_id( 0 ), m_index( 0 ) {}

    _iterator( unsigned ds_id, unsigned index) :
      m_ds_id( ds_id ), m_index( index ) {}

    // copy constructor
    _iterator( const _iterator& it )
      : m_ds_id( it.m_ds_id ), m_index( it.m_index ) {}

    //--------------------------------------------------------------
    // set_state
    //--------------------------------------------------------------

    // set function for ds_id
    void set_state( unsigned ds_id, unsigned index )
    {
      m_ds_id = ds_id;
      m_index = index;
    }
    
    //--------------------------------------------------------------
    // get functions
    // RZ: This is needed because the ASU does cannot return an
    // iterator, it must return a 32bit value. At the very least
    // we need access to m_index
    //--------------------------------------------------------------

    unsigned get_index() const
    {
      return m_index;
    }

    //--------------------------------------------------------------
    // overloaded operators
    //--------------------------------------------------------------

    // assignment
    _iterator& operator=( const _iterator& rhs )
    {
      m_ds_id = rhs.m_ds_id;
      m_index = rhs.m_index;
      return *this;
    }

    // prefix increment
    _iterator& operator++()
    {
      ++m_index;
      return *this;
    }

    // postfix increment
    _iterator operator++( int )
    {
      _iterator tmp( *this );
      operator++();
      return tmp;
    }

    // prefix decrement
    _iterator& operator--()
    {
      --m_index;
      return *this;
    }

    // postfix decrement
    _iterator operator--( int )
    {
      _iterator tmp( *this );
      operator--();
      return tmp;
    }

    // equality compare
    bool operator==( const _iterator& rhs ) const
    {
      return ( m_index == rhs.m_index );
    }

    // not equal compare
    bool operator!=( const _iterator& rhs ) const
    {
      return !( *this == rhs );
    }

    // less than compare
    bool operator<( const _iterator& rhs ) const
    {
      return ( m_index < rhs.m_index );
    }

    // less than equal compare
    bool operator<=( const _iterator& rhs ) const
    {
      return ( m_index <= rhs.m_index );
    }

    // greater than compare
    bool operator>( const _iterator& rhs ) const
    {
      return !( *this <= rhs );
    }

    // greater than equal compare
    bool operator>=( const _iterator& rhs ) const
    {
      return !( *this < rhs );
    }

    // random access operators
    _iterator& operator+=( unsigned i )
    {
      m_index += i;
      return *this;
    }

    _iterator operator+( unsigned i ) const
    {
      _iterator tmp( *this );
      tmp += i;
      return tmp;
    }

    _iterator& operator-=( unsigned i )
    {
      m_index -= i;
      return *this;
    }

    _iterator operator-( unsigned i ) const
    {
      _iterator tmp( *this );
      tmp -= i;
      return tmp;
    }

    // dereference operator will return a ReferenceProxy object
    reference operator*() const
    {
      //return reference( m_ds_id, m_index, &m_iface );
      return reference( m_ds_id, m_index );
    }

}; // end class _iterator

#endif